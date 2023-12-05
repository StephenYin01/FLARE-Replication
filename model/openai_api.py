from typing import List, Dict, Any, Tuple, Union, Set
import os
import json
import openai
import numpy as np

from nltk.tokenize.punkt import PunktSentenceTokenizer
from collections import namedtuple, Counter

from retriever import BM25
from asqa import ASQA

class QueryAgent(object):
    '''
    The QueryAgent queries the OpenAI API.

    Args:
        model (str): The name of the OpenAI API model to query, must be compatible with returning token probabilities
        max_generation_len (int): The maximum number of tokens to generate per API call (should be at least 64, or longer than most sentences)
        temperature (float): Nonnegative parameter controlling randomness of output. As temperature -> 0, the OpenAI output becomes more deterministic
        top_p (float): In [0,1], nucleus sampling. Model only considers tokens with top_p probability mass
        api_key (str): Your personal OpenAI API key
        retriever (BM25): Custom BM25 retriever
        dataset (Any): This stores the dataset we are working with, default ASQA
        retrieval_kwargs (Dict[str, Any]): Hyperparameters of the model to tune

    Attributes:
        model (str): This stores the OpenAI API model name
        max_gen_len (int): This stores the maximum tokens generated per API call
        temperature (float): This stores the temperature for API calls
        top_p (float): This stores the parameter for nucleus sampling for the API calls
        api_key (str): Your personal OpenAI API key 
        psentencizer : The PunktSentenceTokenizer
        min_sent_len (int): This stores the minimum sentence length acceptable for generation
        look_ahead_filter_prob (float): This stores theta, the probability threshold for a token below which triggers retrieval
        look_ahead_mask_prob (float): This stores beta, the probability threshold for tokens below which masks the token in retrieval
        topk_retriever (int): This stores the number of documents for the retriever to retrieve per call
        retriever (BM25): This stores the custom BM25 retriever
        dataset (Any): This stores the dataset we are working with, default ASQA

    '''
    def __init__(
        self, 
        model: str = 'text-davinci-003',
        max_generation_len: int = 64,
        temperature: float = 0,
        top_p: float = 1,
        api_key: str = None,
        retriever: object = BM25(),
        dataset: object = ASQA(),
        retrieval_kwargs: Dict[str, Any] = {},
    ):

        # API call parameters
        self.model = model
        self.max_gen_len = max_generation_len
        self.temperature = temperature
        self.top_p = top_p
        self.api_key = api_key
        
        # Set API key
        openai.api_key = self.api_key

        # Tokenizer
        self.psentencizer = PunktSentenceTokenizer()

        # Parameters for generation
        self.min_sent_len = 5
        self.look_ahead_filter_prob = retrieval_kwargs.get('look_ahead_filter_prob', 0)
        self.look_ahead_mask_prob = retrieval_kwargs.get('look_ahead_mask_prob', 0)
        self.topk_retriever = retrieval_kwargs.get('topk_retriever', 1)

        # Retriever
        self.retriever = BM25(index_name='wikipedia_dpr')

        # Dataset
        self.dataset = dataset

        # Track analytics 
        self._total_api_calls = 0
        self._total_retrieval_calls = 0
        self._low_probability_tokens = Counter()
        self._masked_tokens = Counter()

    def respond(
        self,
        user_inputs: List[str] = None,
    ):
        '''Calls the Complete API for an OpenAI model, and uses the FLARE framework to iteratively query until generation is complete
        
        Args:
            user_inputs (List[str]): The initial queries from the user for the model to answer

        Returns:
            responses (List[str]): The responses to the user's queries
        '''

        bs = len(user_inputs)
        responses = np.array(["" for _ in range(bs)])
        next_inputs = np.array(["" for _ in range(bs)])

        # 1.1 We bootstrap generation by retrieving for the input, and generate the first sentence.
        ctx_ids, ctx_texts = self.retriever.retrieve(user_inputs, topk=self.topk_retriever)
        
        # Set up the documents according to Appendix D.1 in FLARE paper
        next_inputs = self._linearize_documents(ctx_texts, user_inputs, responses)
        
        # Call the OpenAI API and get the first sentences
        first_sents, _, _ = self._complete(next_inputs)
        
        # Update the final responses
        responses = np.char.add(responses, first_sents)
        
        SAFEGUARD_SENTINEL = 0

        while(True):
            
            SAFEGUARD_SENTINEL += 1

            # 1.2 Then, we DO NOT use the retrieved documents and generate the next forward looking sentence(s)
            next_inputs = self._linearize_documents([[] for _ in range(bs)], user_inputs, responses)
            next_sents, all_tok_probs, all_toks = self._complete(next_inputs)
            
            if next_sents == ["" for _ in range(bs)]:
                self._total_api_calls -= bs
                break

            # Update the responses through one iteration of active retrieval
            responses = self._iterative_generate(user_inputs, responses, next_sents, all_tok_probs, all_toks)

            if SAFEGUARD_SENTINEL > 15:
                break

        return self.normalize(list(responses))

    def _complete(self, texts):
        '''Calls the Complete API once for an OpenAI API model
        
        Args:
            texts (List[str]): The texts for the model to complete

        Returns:
            completions (List[str]): The completions to the texts
            all_tok_probs (List[List[float]]): List of list of probabilities associated with generating each token
            all_toks (List[List[float]]): List of list of tokens generated
        '''

        # Call the OpenAI API 
        response = openai.Completion.create(
            model=self.model,
            prompt=texts,
            max_tokens=self.max_gen_len,
            temperature=self.temperature,
            top_p=self.top_p,
            logprobs=0,
        )

        completions = []
        all_tok_probs = []
        all_toks = []

        for i in range(len(texts)):

            # For each text, find the relevant information
            tok_logprobs = response['choices'][i]['logprobs']['token_logprobs']
            text_offset = response['choices'][i]['logprobs']['text_offset']
            toks = response['choices'][i]['logprobs']['tokens']
            tok_probs = np.exp(tok_logprobs)
            str_response = response['choices'][i]['text']
            finish_reason = response['choices'][i]['finish_reason']
            # tokens_used = response['usage']['total_tokens']

            # Handle finish_reason
            if finish_reason == 'content_filter':
                raise Exception('Request hit OpenAI API content filter!')

            # Extract the first sentence
            completion, break_at = self._extract_sentence(str_response)

            # Check if done generating
            if completion == "":
                completions.append(completion)
                all_tok_probs.append(tok_probs)
                all_toks.append(toks)
            else:
                # Find breakpoint to cut off tok_probs and toks
                init_offset = text_offset[0]
                trunc_at = 0

                for j in range(len(text_offset)):
                    trunc_at += 1
                    if text_offset[j] - init_offset >= break_at:
                        trunc_at -= 1
                        break
                    
                # Append to outputs
                completions.append(completion)
                all_tok_probs.append(tok_probs[:trunc_at])
                all_toks.append(toks[:trunc_at])

                # ANALYTICS
                self._total_api_calls += 1

        return completions, all_tok_probs, all_toks

    def _extract_sentence(self, text):
        '''Extracts a sentence from a given text.

        Args:
            text (str): The string to extract the first sentence from

        Returns:
            sent (str): The first sentence of the text
            break_at (int): The breakpoint of the first sentence
        ''' 

        # Set up sentences
        Sentence = namedtuple('Sentence', 'text start_char end_char')
        sents = [Sentence(text[s:e], s, e) for s, e in self.psentencizer.span_tokenize(text)]

        # Remove whitespace at end of sentence which is usually tokenized into next token of sentence by OpenAI API
        break_at = 0

        for sent in sents:

            # Remove the whitespace and check if the sentence satisfies a minimum length
            num_trail_spaces = len(sent.text) - len(sent.text.rstrip())
            break_at = sent.end_char - num_trail_spaces
            if break_at >= self.min_sent_len:
                break

        return text[:break_at], break_at

    def _linearize_documents(self, documents, user_inputs, texts):
        '''Linearizes the context documents according to Appendix D.1 in the FLARE paper

        Ex.
        Search results:
        [1] Document 1
        [2] Document 2
        ...
        (The user input x)(Output generated thus far)

        Args:
            documents (List[List[str]]): The context documents to prefix the text formatted according to Appendix D.1
            user_inputs (List[str]): The user input queries
            texts (List[str]): The texts generated thus far

        Returns:
            linearized_documents (List[str]): The linearized outputs to pass into the LM
        '''

        assert(len(documents) == len(user_inputs) == len(texts))

        bs = len(documents)
        linearized_documents = ["" for _ in range(bs)]

        for i in range(bs):

            _lin_doc = ""

            # In case there is no context
            if list(documents[i]):
                _lin_doc += "Search results:\n"

            for idx, document in enumerate(documents[i]):

                _lin_doc += f"[{idx+1}] {document}\n"

            _lin_doc = self.dataset.construct_query(_lin_doc, user_inputs[i])
            _lin_doc += texts[i]

            linearized_documents[i] = _lin_doc

        return linearized_documents


    def _iterative_generate(self, user_inputs, responses, sents, all_tok_probs, all_toks):
        '''Runs one iteration of active retrieval generation
        
        Args:
            user_inputs (List[str]): The initial queries from the user for the model to answer
            responses (List[str]): The responses generated thus far to the user's queries
            sents (List[str]): The sentences just generated
            all_tok_probs (List[List[float]]): List of list of probabilities associated with generating each token
            all_toks (List[List[float]]): List of list of tokens generated

        Returns:
            responses (List[str]): The responses generated thus far + sentences generated following the FLARE framework
        '''

        assert(len(sents) == len(all_tok_probs) == len(all_toks))

        next_sents = []
        queries = []
        activated_idxs = []
        bs = len(sents)

        # Prepare the queries to the retriever
        for i in range(bs):

            # If we generate a sentence that has low probability tokens, use retrieval and append documents to input + content generated thus far
            # Q: Where do we put exemplars in our response? A: Keep exemplars at the beginning and sandwich retrieved docs
            if sents[i] != "" and min(all_tok_probs[i]) < self.look_ahead_filter_prob:

                # Implicity query by masking
                _mask = np.array(all_tok_probs[i]) < self.look_ahead_mask_prob
                query = np.where(_mask, "", all_toks[i])
                query = "".join(query)

                # Remove whitespace in beginning of query
                query = query.lstrip()

                queries.append(query)
                activated_idxs.append(i)
                next_sents.append("")

                # ANALYTICS
                self._total_retrieval_calls += 1
                self._total_api_calls -= 1 # or else API Calls double counted from self._complete below
                
                _mask2 = np.array(all_tok_probs[i]) < self.look_ahead_filter_prob
                self._masked_tokens.update(np.array(all_toks[i])[_mask])
                self._low_probability_tokens.update(np.array(all_toks[i])[_mask2])


            else:
                next_sents.append(sents[i])

        if queries:
            
            # Batch retrieve
            ctx_ids, ctx_texts = self.retriever.retrieve(queries, topk=self.topk_retriever)
            next_inputs = self._linearize_documents(ctx_texts, np.array(user_inputs)[activated_idxs], np.array(responses)[activated_idxs])
            
            # Make sure to only complete for queries where retrieval was necessary
            gen_sents, _, _ = self._complete(next_inputs)

            # Update the final responses, making sure to remember which queries activated retrieval
            c = 0
            for i in range(bs):
                if i in activated_idxs:
                    next_sents[i] = gen_sents[c]
                    c += 1
                
        responses = np.char.add(responses, next_sents)

        return responses

    def normalize(self, responses):
        '''Normalizes the output of the model
        
        Args:
            responses (List[str]): The responses generated to the user's queries

        Returns:
            normalized (List[str]): The normalized responses
        '''

        # Lower case the responses and remove leading whitespace
        normalized = [x.lower().lstrip() for x in responses]

        return normalized

    def _display_analytics(self):
        '''Displays analytics of the model

        Args:
            None
        
        Returns:
            None
        '''

        # Print 
        print(f"Total API calls: {self._total_api_calls}")
        print(f"Total Retrievals: {self._total_retrieval_calls}")
        print(f"Retrieval Rate: {self._total_retrieval_calls/self._total_api_calls}")
        print('─' * 20)
        print(f"Most common low probability tokens: {self._low_probability_tokens.most_common(10)}")
        print(f"Most common masked tokens for implicit retrieval: {self._masked_tokens.most_common(10)}")
        print(f"Total num low probability tokens: {self._low_probability_tokens.total()}")
        print(f"Total num masked tokens for implicit retrieval: {self._masked_tokens.total()}")

    def _save_analytics(self, path):
        '''Save model analytics to the specified path

        Args:
            path (str): The path to save analytics of model to

        Returns:
            None
        '''

        cur_path = os.path.abspath(os.curdir)

        data = {
            "api_calls": self._total_api_calls,
            "retrieval_calls": self._total_retrieval_calls,
            "low_prob_toks": self._low_probability_tokens,
            "low_masked_toks": self._masked_tokens,
        }

        with open(cur_path + path, 'w') as f:
            json.dump(data, f)