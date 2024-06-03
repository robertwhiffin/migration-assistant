import os

from openai import OpenAI

from app.table_metadata import build_table_metadata
# details for connecting to the llm endpoint

# the URL of the serving endpoint
MODEL_SERVING_ENDPOINT_URL = f"https://{os.environ['DATABRICKS_HOST']}/serving-endpoints"
client = OpenAI(
  api_key=os.environ["DATABRICKS_TOKEN"],
  base_url=MODEL_SERVING_ENDPOINT_URL
)


################################################################################
################################################################################
# this is called to actually send a request and receive response from the llm endpoint.

def ask_llm(metadata_prompt, no_metadata_prompt, sql_query):
    table_descriptions = build_table_metadata(sql_query)
    if table_descriptions:
        # set the system prompt
        system_prompt = metadata_prompt
        # build the query prompt by adding code and metadata descriptions
        query_prompt = f"This is the SQL code: {sql_query}. \n\n{table_descriptions}"
    else:
        system_prompt = no_metadata_prompt
        # build the query prompt by adding code and metadata descriptions
        query_prompt = f"This is the SQL code: {sql_query}"

    # call the LLM end point.
    chat_completion = client.chat.completions.create(
        messages=[
        {"role": "system", "content": system_prompt}
        ,{"role": "user",  "content": query_prompt}
        ],
        model=os.environ["SERVED_MODEL_NAME"],
        max_tokens=int(os.environ["MAX_TOKENS"])
    )

    # helpful for debugging -show the query sent to the LLM
    #return [chat_completion.choices[0].message.content, query_prompt]
    # this is the return without the chat interface
    #return chat_completion.choices[0].message.content
    # this is the return for the chatbot - empty string to fill in the msg, list of lists for the chatbot
    return "", [[query_prompt, chat_completion.choices[0].message.content]]


def call_llm_for_chat(chat_history, query, metadata_prompt, no_metadata_prompt, sql_query):
    table_descriptions = build_table_metadata(sql_query)
    if table_descriptions:
        # set the system prompt
        system_prompt = metadata_prompt
        # build the query prompt by adding code and metadata descriptions
        query_prompt = f"This is the SQL code: {sql_query}. \n\n{table_descriptions}"
    else:
        system_prompt = no_metadata_prompt
        # build the query prompt by adding code and metadata descriptions
        query_prompt = f"This is the SQL code: {sql_query}"
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
        model=os.environ["SERVED_MODEL_NAME"],
        max_tokens=int(os.environ["MAX_TOKENS"])
    )
    return chat_completion.choices[0].message.content

