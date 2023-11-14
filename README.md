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


### Download ASQA dataset

Follow the instructions from [the ASQA repository](https://github.com/google-research/language/tree/master/language/asqa). Rename the ASQA dataset to ```ASQA_full.json``` and place it in the directory ```dataset/ASQA_full.json```

Then, create the test set by subsampling from the ```dev``` split of ASQA:
```
python setup/select_questions.py
```

### Download Wikipedia dump
Download the Wikipedia dump from [the DPR repository](https://github.com/facebookresearch/DPR/blob/main/dpr/data/download_data.py#L32) using the following command:
```shell
mkdir dataset/dpr
wget -O dataset/dpr/psgs_w100.tsv.gz https://dl.fbaipublicfiles.com/dpr/wikipedia_split/psgs_w100.tsv.gz
pushd dataset/dpr
gzip -d psgs_w100.tsv.gz
popd
```

### Build the ElasticSearch index

Run the following command to build the ElasticSearch index

```
python setup/build_index.py --datapath dataset/dpr/psgs_w100.tsv
```

There are 21,015,325 documents in the wikipedia dump to load.

## Run the model to generate results

__⚠️WARNING⚠️: Running the model makes many queries to the OpenAI API, which can result in ~$25 per experiment on 500 examples.__

### Generate the results

Run the following command to generate results on the selected test set

``` 
python model/flare.py
```

The results should be saved in ```outputs/{EXP_NAME_DEFINED_IN_FLARE.PY}.json```


### Evaluate the results

Outputs should be correctly formatted such that one can follow the instructions from the [ASQA repo](https://github.com/google-research/language/tree/master/language/asqa#automatic-evaluation).

Example results for the reimplementation of FLARE_direct with implicit queries:

```json
{
    "rougeLsum": 27.630332229755194, 
    "length": 136.802, 
    "str_em": 40.75, 
    "QA-EM": 18.246666666666663, 
    "QA-F1": 24.25903202141283, 
    "QA-Hit": 2.6, 
    "ovscore": 25.88986508894757
}
```