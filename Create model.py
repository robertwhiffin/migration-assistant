# Databricks notebook source
# MAGIC %pip install langchain databricks-vectorsearch databricks-sdk sqlalchemy
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# from langchain.chat_models import ChatDatabricks
# chat_model = ChatDatabricks(endpoint="databricks-meta-llama-3-70b-instruct", max_tokens = 2000)
# print(f"Test chat model: {chat_model.predict('What is the role of the Central Bank of Ireland?')}")

# COMMAND ----------

chat_history =[["q", "a"]]
chat_history[-1][0]

# COMMAND ----------

from langchain_community.chat_models import ChatDatabricks
from langchain.schema.runnable import RunnableLambda
from langchain.schema.output_parser import StrOutputParser
from mlflow.deployments import get_deploy_client
from langchain.prompts import PromptTemplate
from operator import itemgetter

#The question is the last entry of the history
def extract_question(input):
    return input[-1]["content"]

#The history is everything before the last question
def extract_history(input):
    return input[:-1]
  
prompt_with_history_str = """
Your are a chatbot which helps users to understand the intent of their SQL code. 

Here is a history between you and a human: {chat_history}

Now, please answer this question: {question}
"""

prompt_with_history = PromptTemplate(
  input_variables = ["chat_history", "question"],
  template = prompt_with_history_str
)

chat_model = ChatDatabricks(endpoint="databricks-meta-llama-3-70b-instruct", max_tokens = 2000)

chain_with_history = (
    {
        "question": itemgetter("messages") | RunnableLambda(extract_question),
        "chat_history": itemgetter("messages") | RunnableLambda(extract_history),
    }
    | prompt_with_history
    | chat_model
    | StrOutputParser()
)
print(chain_with_history.invoke({
    "messages": [
        {"role": "user", "content": "What is Apache Spark?"}, 
        {"role": "assistant", "content": "Apache Spark is an open-source data processing engine that is widely used in big data analytics."}, 
        {"role": "user", "content": "Does it support streaming?"}
    ]
}))

# COMMAND ----------


from langchain.prompts import PromptTemplate
prompt = PromptTemplate(
  input_variables = ["question"],
  template = "You are an assistant. Give a short answer to this question: {question}"
)
chat_model = ChatDatabricks(endpoint="databricks-meta-llama-3-70b-instruct", max_tokens = 2000)

chain = (
  prompt
  | chat_model
  | StrOutputParser()
)
print(chain.invoke({"question": "What is Spark?"}))

# COMMAND ----------


from openai import OpenAI
import os
from utils.configloader import configLoader
cl = configLoader() 
cl.read_yaml_to_env("config.yaml")
# # personal access token necessary for authenticating API requests. Stored using a secret
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
DATABRICKS_HOST = os.environ["DATABRICKS_HOST"]

# details for connecting to the llm endpoint

# the URL of the serving endpoint
MODEL_SERVING_ENDPOINT_URL = f"https://{DATABRICKS_HOST}/serving-endpoints"

client = OpenAI(
  api_key=DATABRICKS_TOKEN,
  base_url=MODEL_SERVING_ENDPOINT_URL
)


client = OpenAI(
  api_key=DATABRICKS_TOKEN,
  base_url=MODEL_SERVING_ENDPOINT_URL
)


def call_llm(chat_history, query):
    system_prompt = "You are a chatbot which helps users explain the intent of their code."
    messages=[
        {"role": "system", "content": system_prompt}
        ] 
    for q, a in chat_history:
      messages.extend(
        [{"role": "user",  "content": q}
        ,{"role": "assistant",  "content": a}]
        )
    messages.append(
        {"role": "user",  "content": query})
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="databricks-meta-llama-3-70b-instruct",
        max_tokens=int(2000)
    )
    return chat_completion.choices[0].message.content

# COMMAND ----------

messages=[
        {"role": "system", "content": "hello"}
        ] 
messages.extend(
  [{"role": "user",  "content": "q"}
  ,{"role": "assistant",  "content": "a"}]
  )

messages.append(
  {"role": "user",  "content": "query"})
messages

# COMMAND ----------

call_llm(
  [["Who won the world series in 2020?", "The Los Angeles Dodgers won the World Series in 2020"]]
  ,"Where was it played?"
)
