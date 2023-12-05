import json
import random

# Set the seed
random.seed(42)

# Load and select the questions
file = "dataset/ASQA_full.json"

with open(file, 'r') as f:
    asqa = json.load(f)

sizes = [500, 50]
names = ["ASQA", "ASQA_mini"]

for i in range(len(sizes)):
    # Exemplars are all in train set, so no need to worry about exemplars including test and contaminating results
    questions = random.sample(sorted(asqa['dev']), k=sizes[i])

    # Create the testing examples
    asqa_subsample = dict()
    asqa_subsample['dev'] = dict()

    for qid in questions:
        asqa_subsample['dev'][qid] = asqa['dev'][qid]

    # Store as json
    json_file = f"dataset/{names[i]}.json"
    with open(json_file, "w") as f:
        json.dump(asqa_subsample, f)
