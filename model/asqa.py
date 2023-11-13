from typing import List, Dict

class ASQA(object):

    def __init__(
        self, 
        num_exemplars=8
    ):

        self.num_exemplars = num_exemplars
        
        # hint_template = lambda self, ques: f'Given an ambiguous question and a hint on which aspect of the question is ambiguous, figure out its interpretations and answer them one by one.\nQuestion: {ques}\nAnswer: In order to figure out its interpretations,'
        self.question_template = lambda ques: f'Given an ambiguous question, figure out its interpretations and answer them one by one.\nQuestion: {ques}\nAnswer:'
        self.ans_template = lambda general_hint, subq_cot, answer: f" {general_hint} In order to figure out its interpretations, {subq_cot} {answer}"
        self.ctx_initialized = False
        self.ctx = None

        self.general_hint_in_input_examplars: List[Dict] = [
        {
            "id": "-6681997980074150658",
            "question": "Who played bonnie in gone with the wind?",
            "category": "entity",
            "hint_me": "This question is ambiguous because Gone with the Wind refers to multiple entities.",
            "general_hint": "This question is ambiguous in terms of which version or adaptation of Gone with the Wind is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify which version of Gone with the Wind is being referred to, and therefore could be interpreted as asking about either the 1939 film or the 2008 musical.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific film adaptation, as it could refer to either the 1939 film or the 2008 musical adaptation.",
            "subq_cot": "we need to consider different versions or adaptations of Gone with the Wind. Gone with the Wind has two versions or adaptations: the 1939 film Gone with the Wind or the 2008 musical Gone with the Wind.",
            "answer": "Therefore, this question has 2 interpretations: (1) Who played Bonnie in the 1939 film Gone with the Wind? (2) Who played Bonnie in the 2008 musical Gone with the Wind? The answers to all interpretations are: (1) The 1939 film Gone with the Wind\'s character Bonnie was played by Eleanore Cammack \"Cammie\" King. (2) The 2008 musical Gone with the Wind\'s character Bonnie was played by Leilah de Meza.",
        },
        {
            "id": "-1170854568854448296",
            "question": "What is the second largest city in the usa?",
            "category": "event",
            "hint_me": "This question is ambiguous because city size can be measured in multiple ways.",
            "general_hint": "This question is ambiguous in terms of the criteria being used to determine the second largest city in the USA.",
            "specific_hint": "This question is ambiguous as it does not specify whether the second largest city in the USA is being referred to by population or by area, and therefore could be interpreted as asking about either aspect.",
            "specific_hint_keyword": "This question is ambiguous in terms of the criteria used to determine the second largest city in the USA, as it could refer to either population or area.",
            "subq_cot": "we need to consider different criteria to determine a city's size. City size can be measured by two criteria: population or area.",
            "answer": "Therefore, this question has 2 interpretations: (1) What is the second largest city in the USA by population? (2) What is the second largest city in the USA by area? The answers to all interpretations are: (1) The second largest city in the USA by population is Los Angeles, California. (2) The second largest city in the USA by area is Juneau, Alaska.",
        },
        {
            "id": "-42361505900466516",
            "question": "When was bohemian rhapsody released as a single?",
            "category": "context",
            "hint_me": "This question is ambiguous because it has different answers in different countries.",
            "general_hint": "This question is ambiguous in terms of which country's release of the single is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify in which country Bohemian Rhapsody was released as a single, and therefore could be interpreted as asking about either the United Kingdom or the United States.",
            "specific_hint_keyword": "This question is ambiguous in terms of the geographic location of the release, as it could refer to either the United Kingdom or the United States.",
            "subq_cot": "we need to consider different countries where Bohemian Rhapsody is released. Bohemian Rhapsody was released in the United Kingdom and in the United States on different dates.",
            "answer": "Therefore, this question has 2 interpretations: (1) When was Bohemian Rhapsody released as a single in the United Kingdom? (2) When was Bohemian Rhapsody released as a single in the United States? The answers to all interpretations are: (1) Bohemian Rhapsody was released as a single in the United Kingdom on 31 October 1975. (2) Bohemian Rhapsody was released as a single in the United States on December 1975."
        },
        {
            "id": "-6158441934367575013",
            "question": "Where do the philadelphia eagles play their home games?",
            "category": "answer_type",
            "hint_me": "This question is ambiguous because there are multiple interpretations of the home field of the Philadelphia Eagles.",
            "general_hint": "This question is ambiguous in terms of which specific location or venue is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify which aspect of the Philadelphia Eagles' home games is being referred to, and therefore could be interpreted as asking about the city, sports complex, or stadium where they play their home games.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific location of the Philadelphia Eagles' home games, as it could refer to the city, sports complex, or stadium.",
            "subq_cot": "we need to consider the different possible locations or venues that could be considered the home field of the Philadelphia Eagles. These include the city, the sports complex, or the stadium.",
            "answer": "Therefore, this question has 3 interpretations: (1) What city do the Philadelphia Eagles play their home games? (2) In what sports complex do the Philadelphia Eagles play their home games? (3) What stadium do the Philadelphia Eagles play their home games? The answers to all interpretations are: (1) Philadelphia Eagles play their home games in the city Philadelphia. (2) Philadelphia Eagles play their home games in the South Philadelphia Sports Complex. (3) Philadelphia Eagles play their home games in the Lincoln Financial Field stadium.",
        },

        {
            "id": "7925778961305870115",
            "question": "When did xbox one come out in australia?",
            "category": "entity",
            "hint_me": "This question is ambiguous because Xbox One refers to multiple entities.",
            "general_hint": "This question is ambiguous in terms of which specific version of the Xbox One is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify which version of the Xbox One is being referred to, and therefore could be interpreted as asking about either the original Xbox One or the Xbox One X.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific Xbox One model release, as it could refer to either the original Xbox One or the Xbox One X.",
            "subq_cot": "we need to consider the different versions of the Xbox One that have been released. Xbox One has two versions: the Xbox One video game console or the Xbox One X high-end model.",
            "answer": "Therefore, this question has 2 interpretations: (1) When did the Xbox One release in Australia? (2) When did the Xbox One X release in Australia? The answers to all interpretations are: (1) The Xbox One video game console was released in Australia on November 22, 2013. (2) The Xbox One X video game console was released in Australia on November 7, 2017.",
        },
        {
            "id": "-5527347701597533393",
            "question": "When does the movie summer of 84 come out?",
            "category": "event",
            "hint_me": "This question is ambiguous because a movie might come out on different dates depending on the context.",
            "general_hint": "This question is ambiguous in terms of which release of the movie is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify which release of the movie Summer of '84 is being referred to, and therefore could be interpreted as asking about either its release at the Sundance Festival or its release throughout the US.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific release of the movie Summer of '84, as it could refer to either the release date at the Sundance Festival or the release date throughout the US.",
            "subq_cot": "we need to consider different releases of the movie Summer of '84. The movie Summer of '84 is first released at the Sundance Festival before it's released throughout the US.",
            "answer": "Therefore, this question has 2 interpretations: (1) When did the movie Summer of '84 first release at the Sundance Festival? (2) When did the movie Summer of '84 first release throughout the US? The answers to all interpretations are: (1) Summer of '84 was released at the Sundance Festival on January 22, 2018. (2) Summer of '84 was released throughout the US on August 10, 2018.",
        },
        {
            "id": "8423232783444896189",
            "question": "What was roy orbison's first number one hit?",
            "category": "context",
            "hint_me": "This question is ambiguous because it has different answers in different countries.",
            "general_hint": "This question is ambiguous in terms of which specific chart or region is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify in which countries or regions Roy Orbison's first number one hit is being referred to, and therefore could be interpreted as asking about either the US Hot 100 and Canada or the UK and Ireland.",
            "specific_hint_keyword": "This question is ambiguous in terms of the geographic location of the chart where Roy Orbison's first number one hit is being referred to, as it could refer to either the US Hot 100 and Canada or the UK and Ireland.",
            "subq_cot": "we need to consider the different charts and regions where Roy Orbison's music was popular. Roy Orbison is popular in both the US Hot 100 and Canada, and the UK and Ireland.",
            "answer": "Therefore, this question has 2 interpretations: (1) What was Roy Orbison's first number one hit in the US Hot 100 and Canada? (2) What was Roy Orbison's first number one hit in the UK and Ireland? The answers to all interpretations are: (1) Running Scared was the first number one hit for Roy Orbison in the US Hot 100 and Canada. (2) Only the Lonely (Know the Way I Feel) was the first number one hit for Roy Orbison in the UK and Ireland.",
        },
        {
            "id": "3471060247311635100",
            "question": "What is the criminal's name in the breakfast club?",
            "category": "answer_type",
            "hint_me": "This question is ambiguous because there are multiple interpretations of the criminal's name.",
            "general_hint": "This question is ambiguous in terms of which specific name is being referred to - the character's name or the actor's name.",
            "specific_hint": "This question is ambiguous as it does not specify which aspect of the criminal in The Breakfast Club is being referred to, and therefore could be interpreted as asking about either the character's name or the actor's name who played the character.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific identity of the criminal in The Breakfast Club, as it could refer to either the character name or the actor who played the role.",
            "subq_cot": "we need to consider both possibilities: the character's name or the actor's name.",
            "answer": "Therefore, this question has 2 interpretations: (1) What is the criminal's character name in The Breakfast Club? (2) What is the the name of the actor who played the criminal in The Breakfast Club? The answers to all interpretations are: (1) John Bender was the name of the criminal's character in The Breakfast Club. (2) Judd Nelson was the actor of the criminal in The Breakfast Club.",
        },


        {
            "id": "-6497998034447212269",
            "question": "When did bat out of hell come out?",
            "category": "entity",
            "hint_me": "This question is ambiguous because Bat out of Hell refers to multiple entities.",
            "general_hint": "This question is ambiguous in terms of which specific version or adaptation of Bat Out of Hell is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify which version of Bat Out of Hell is being referred to, and therefore could be interpreted as asking about either the album or the TV series.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific media format of Bat Out of Hell, as it could refer to either the album or the TV series.",
            "subq_cot": "we need to consider the different versions or adaptations of Bat Out of Hell. Bat Out of Hell has two versions or adaptations: the album Bat Out of Hell or the TV series Bat Out of Hell.",
            "answer": "Therefore, this question has 2 interpretations: (1) When did the album Bat Out of Hell come out? (2) When did the TV series Bat Out of Hell come out? The answers to all interpretations are: (1) The album Bat Out of Hell came out on October 21, 1977. (2) The British television show Bat Out of Hell came out on 26 November 1966.",
        },
        {
            "id": "4370113190341229231",
            "question": "When was smoking banned in new york city?",
            "category": "event",
            "hint_me": "This question is ambiguous because smoking ban in NYC happened progressively and it has multiple interpretations.",
            "general_hint": "This question is ambiguous in terms of which specific smoking ban in New York City is being referred to.",
            "specific_hint": "This question is ambiguous as it does not specify which aspect of smoking ban in New York City is being referred to, and therefore could be interpreted as asking about the ban on indoor smoking, the statewide smoking ban, the ban on smoking in parks and rec centers, or the ban on smoking for anyone under 21.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific smoking ban being referred to, as it could refer to the ban on indoor smoking, the statewide smoking ban, the ban on smoking in parks and rec centers, or the ban on smoking for anyone under 21 in NYC.",
            "subq_cot": "we need to consider the different smoking bans that have been implemented in New York City. Smoking ban in NYC has multiple implementations: indoor smoking ban, statewide smoking ban, smoking ban in parks and rec centers, or smoking ban for anyone under 21.",
            "answer": "Therefore, this question has 4 interpretations: (1) When was indoor smoking banned in NYC? (2) When did New Yorks statewide smoking ban go into effect? (3) When was smoking in parks and rec centers banned in NYC? (4) When was anyone under 21 banned from smoking in NYC? The answers to all interpretations are: (1) Indoor smoking in NYC was banned on March 30, 2003. (2) New York went to a state wide ban on July 24, 2003. (3) Smoking was banned in NYC parks and rec centers on May 23, 2011. (4) NYC banned smoking for anyone under the age of 21 on May 18, 2014.",
        },
        {
            "id": "-4377718773044986307",
            "question": "New zealand is a part of what continent?",
            "category": "context",
            "hint_me": "This question is ambiguous because it has different answers in different history period.",
            "general_hint": "This question is ambiguous in terms of whether it is asking about the current or historical continental location of New Zealand.",
            "specific_hint": "This question is ambiguous as it does not specify which aspect of New Zealand's continental history is being referred to, and therefore could be interpreted as asking about either its current microcontinent or its past supercontinent before the Jurassic period.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific geographic context being referred to, as it could refer to the microcontinent that New Zealand is a part of or the supercontinent that New Zealand was a part of until the Jurassic period.",
            "subq_cot": "we need to consider both possibilities: current or historical continental location. The contient of New Zealand is different before and after Jurassic period.",
            "answer": "Therefore, this question has 2 interpretations: (1) New Zealand is a part of what microcontienent? (2) New Zealand was a part of what supercontinent until the Jurassic period? The answers to all interpretations are: (1) New Zealand is currently part of a continent called Zealandia. (2) New Zealand was a part of Gondwana until the Jurassic period.",
        },
        {
            "id": "8905159142292415847",
            "question": "Who sings i stand alone in quest for camelot?",
            "category": "answer_type",
            "hint_me": "This question is ambiguous because there are multiple interpretations of the singer.",
            "general_hint": "This question is ambiguous in terms of which specific type of performer is being referred to - the character or the artist.",
            "specific_hint": "This question is ambiguous as it does not specify which aspect of the song \"I Stand Alone\" in Quest for Camelot is being referred to, and therefore could be interpreted as asking about either the character who sings the song or the artist who performs the song.",
            "specific_hint_keyword": "This question is ambiguous in terms of the specific identity of the singer of I Stand Alone in Quest for Camelot, as it could refer to either the character or the artist who performed the song.",
            "subq_cot": "we need to consider both possibilities: the character or the artist.",
            "answer": "Therefore, this question has 2 interpretations: (1) Which character sings I Stand Alone in Quest for Camelot? (2) Which artist sings I Stand Alone in Quest for Camelot? The answers to all interpretations are: (1) The character sings I Stand Alone in Quest for Camelot is King Arthur. (2) The artist sings I Stand Alone in Quest for Camelot is Steve Perry.",
        }
        ]

    def construct_exemplars(self):
        '''Constructs the exemplars for the ASQA task

        Returns:
            exemplars (str): The string of exemplars to prefix input
        '''

        exemplars = ""

        for i in range(self.num_exemplars):
            exemplars += self.question_template(self.general_hint_in_input_examplars[i]['question'])
            exemplars += self.ans_template(
                self.general_hint_in_input_examplars[i]['general_hint'],
                self.general_hint_in_input_examplars[i]['subq_cot'],
                self.general_hint_in_input_examplars[i]['answer']
            )
            exemplars += "\n\n"

        self.ctx = exemplars

        # Update initialized flag
        self.ctx_initialized = True

        return exemplars

    def construct_query(self, context, question):
        '''Adds the question after constructing the exemplars

        Args:
            question (str): The user input question

        Returns:
            query (str): The user question prefixed by the exemplars and templates
        '''

        if not self.ctx_initialized:
            query = self.construct_exemplars()
        else:
            query = self.ctx

        query += context
        query += self.question_template(question)

        return query