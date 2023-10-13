import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.Completion.create(
  model="gpt-3.5-turbo-instruct",
  prompt="The following question is ambiguous, so there are multiple interpretations of the question. Please write a response that answers all interpretations of the question: Who has the record for most super bowl losses?",
  temperature=1.25,
  max_tokens=400,
  top_p=1,
  frequency_penalty=0.25,
  presence_penalty=0.1,
  logprobs=1
)

print(response)