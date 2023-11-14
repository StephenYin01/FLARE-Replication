from typing import List, Dict, Tuple
import time
import uuid
import tqdm
import numpy as np

from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.lexical import BM25Search
from beir.retrieval.search.lexical.elastic_search import ElasticSearch

class BM25(object):
    '''
    The BM25 retriever instance.

    Args:
        index_name (str): The ElasticSearch index for the retriever to retriever from.

    Attributes:
        max_ret_topk (int): The maximum number of documents

    '''
    def __init__(
        self,
        index_name: str = 'wikipedia_dpr',
    ):

        self.max_ret_topk = 1000
        self.retriever = EvaluateRetrieval(
            BM25Search(index_name=index_name, hostname='localhost', initialize=False, number_of_shards=1),
            k_values=[self.max_ret_topk]
        )

    def _get_random_doc_id(self):
        return f'_{uuid.uuid4()}'

    def retrieve(
        self,
        queries: List[str],
        topk: int = 1,
    ):
        '''Calls the retriever for the given query and returns the topk results

        Args:
            queries (List[str]): The list of queries from the user for the model to answer
            topk (int): The maximum number of documents to return

        Returns:
            docids (np.array): Shape (bs, topk), the document ids retrieved
            docs (np.array): Shape (bs, topk), the text of the documents retrieved
        '''
        assert topk <= self.max_ret_topk
        bs = len(queries)

        # Retrieve, queries should be Dict[str, str]
        results: Dict[str, Dict[str, Tuple[float, str]]] = self.retriever.retrieve(
            None, dict(zip(range(len(queries)), queries)), disable_tqdm=True)

        # Prepare outputs
        docids: List[str] = []
        docs: List[str] = []

        for qid, query in enumerate(queries):

            # Temporary list of document IDs and document texts
            _docids: List[str] = []
            _docs: List[str] = []

            # If the query yielded results
            if qid in results:
                for did, (score, text) in results[qid].items():
                    _docids.append(did)
                    _docs.append(text)
                    if len(_docids) >= topk:
                        break
            
            # Add dummy docs to reach topk length
            if len(_docids) < topk:  # add dummy docs
                _docids += [self._get_random_doc_id() for _ in range(topk - len(_docids))]
                _docs += [''] * (topk - len(_docs))

            docids.extend(_docids)
            docs.extend(_docs)

        docids = np.array(docids).reshape(bs, topk)  # (bs, topk)
        docs = np.array(docs).reshape(bs, topk)  # (bs, topk)
        return docids, docs

''' We need to modify the implementation of BM25Search to return the text as well as the scores of the search results'''
def bm25search_custom(self, corpus: Dict[str, Dict[str, str]], queries: Dict[str, str], top_k: int, *args, **kwargs) -> Dict[str, Dict[str, float]]:
    
    # Index the corpus within elastic-search
    # False, if the corpus has been already indexed
    if self.initialize:
        self.index(corpus)
        # Sleep for few seconds so that elastic-search indexes the docs properly
        time.sleep(self.sleep_for)

    #retrieve results from BM25
    query_ids = list(queries.keys())
    queries = [queries[qid] for qid in query_ids]

    # ---Custom Code---
    self.results: Dict[str, Dict[str, Tuple[float, str]]] = {}

    for start_idx in tqdm.trange(0, len(queries), self.batch_size, desc='que', disable=kwargs.get('disable_tqdm', False)):
        query_ids_batch = query_ids[start_idx:start_idx+self.batch_size]
        results = self.es.lexical_multisearch(
            texts=queries[start_idx:start_idx+self.batch_size],
            top_hits=top_k)

        for (query_id, hit) in zip(query_ids_batch, results):
            scores = {}
            for corpus_id, score, text in hit['hits']:
                scores[corpus_id] = (score, text)
                self.results[query_id] = scores
    # ---End Custom---

    return self.results

# Modifying BM25Search implementation
BM25Search.search = bm25search_custom

'''We also need to modify the implementation of ElasticSearch in case there are no hits'''
def elasticsearch_lexical_multisearch(self, texts: List[str], top_hits: int, skip: int = 0) -> Dict[str, object]:
    """Multiple Query search in Elasticsearch

    Args:
        texts (List[str]): Multiple query texts
        top_hits (int): top k hits to be retrieved
        skip (int, optional): top hits to be skipped. Defaults to 0.

    Returns:
        Dict[str, object]: Hit results
    """
    request = []

    assert skip + top_hits <= 10000, "Elastic-Search Window too large, Max-Size = 10000"

    for text in texts:
        req_head = {"index" : self.index_name, "search_type": "dfs_query_then_fetch"}
        req_body = {
            "_source": True, # No need to return source objects
            "query": {
                "multi_match": {
                    "query": text, # matching query with both text and title fields
                    "type": "best_fields",
                    "fields": [self.title_key, self.text_key],
                    "tie_breaker": 0.5
                    }
                },
            "size": skip + top_hits, # The same paragraph will occur in results
            }
        request.extend([req_head, req_body])

    res = self.es.msearch(body = request)

    result = []
    for resp in res["responses"]:
        responses = resp["hits"]["hits"][skip:] if 'hits' in resp else []

        hits = []
        for hit in responses:
            hits.append((hit["_id"], hit['_score'], hit['_source']['txt']))

        result.append(self.hit_template(es_res=resp, hits=hits))
    return result

def elasticsearch_hit_template(self, es_res: Dict[str, object], hits: List[Tuple[str, float]]) -> Dict[str, object]:
    """Hit output results template

    Args:
        es_res (Dict[str, object]): Elasticsearch response
        hits (List[Tuple[str, float]]): Hits from Elasticsearch

    Returns:
        Dict[str, object]: Hit results
    """
    result = {
        'meta': {
            'total': es_res['hits']['total']['value'] if 'hits' in es_res else None,
            'took': es_res['took'] if 'took' in es_res else None,
            'num_hits': len(hits)
        },
        'hits': hits,
    }
    return result

# Modifying ElasticSearch implementation
ElasticSearch.lexical_multisearch = elasticsearch_lexical_multisearch
ElasticSearch.hit_template = elasticsearch_hit_template