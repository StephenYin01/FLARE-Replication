import argparse
import time
import csv
from tqdm import tqdm
from beir.retrieval.search.lexical.elastic_search import ElasticSearch

def build_elasticsearch(
    beir_corpus_file_pattern: str,
    index_name: str,
):

    print(f'Building index for {beir_corpus_file_pattern}')
    
    config = {
        'hostname': 'localhost',
        'index_name': index_name,
        'keys': {'title': 'title', 'body': 'txt'},
        'timeout': 100,
        'retry_on_timeout': True,
        'maxsize': 24,
        'number_of_shards': 'default',
        'language': 'english',
    }
    es = ElasticSearch(config)

    # Create index (from BM25Search class)
    print(f'Creating index {index_name}')
    es.delete_index()
    time.sleep(5)
    es.create_index()

    # Generator ( customized ElasticSearch.generate_actions() )
    def generate_actions():

        with open(beir_corpus_file_pattern, 'r') as f:

            reader = csv.reader(f, delimiter='\t')
            header = next(reader) # skip header

            for row in reader:

                _id, text, title = row[0], row[1], row[2]
                es_doc = {
                    '_id': _id,
                    '_op_type': 'index',
                    'refresh': 'wait_for',
                    config['keys']['title']: title,
                    config['keys']['body']: text,
                }

                yield es_doc

    # Index
    progress = tqdm(unit='docs')

    es.bulk_add_to_index(
        generate_actions=generate_actions(),
        progress=progress)

if __name__ == '__main__':
    # Need to know path to wikipedia data .tsv file
    parser = argparse.ArgumentParser()

    parser.add_argument('--datapath', type=str, default=None, required=True, help='Path to corpus data')
    parser.add_argument('--name', type=str, default="wikipedia_dpr",  help='Name of the ElasticSearch index')

    args = parser.parse_args()

    # Build the ElasticSearch index
    beir_corpus_file_pattern = args.datapath
    index_name = args.name

    build_elasticsearch(beir_corpus_file_pattern, index_name=index_name)
