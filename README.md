# Replicating FLARE's results

by Stephen Yin

Github repository to replicate the results from the [FLARE paper results](https://github.com/jzbjyb/FLARE)

## Requirements
This project used Python 3.10.13.

To set up the dependencies, it is recommended to use a virtual environment (conda was used for this project).

1. Run ```bash setup/setup.sh```
1. Retrieve your [OpenAI API key](https://platform.openai.com/account/api-keys). Add the following to your ```~/.bashrc```: ```export OPENAI_API_KEY="{YOUR_API_KEY_HERE}"``` (replace the curly braces as well)

Note: The version of ```sentencepiece``` was changed from ```0.1.83``` to ```0.1.98``` to be compatible with the use of Python 3.10.13.

## Setup (Downloads & Retrieval Engine Building)


### Download ASQA Dataset

Follow the instructions from [the ASQA repository](https://github.com/google-research/language/tree/master/language/asqa)

Then, create the test set by subsampling from the ```dev``` split of ASQA:
```
python setup/select_questions.py
```

### Download Wikipedia dump
Download the Wikipedia dump from [the DPR repository](https://github.com/facebookresearch/DPR/blob/main/dpr/data/download_data.py#L32) using the following command:
```shell
mkdir data/dpr
wget -O data/dpr/psgs_w100.tsv.gz https://dl.fbaipublicfiles.com/dpr/wikipedia_split/psgs_w100.tsv.gz
pushd data/dpr
gzip -d psgs_w100.tsv.gz
popd
```

### Build the ElasticSearch index

Run the following command to build the ElasticSearch index

```
python setup/build_index.py --datapath dataset/dpr/psgs_w100.tsv
```

There are 21,015,325 documents in the wikipedia dump to load.
