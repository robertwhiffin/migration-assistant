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

model=os.environ["SERVED_MODEL_NAME"]
def call_llm(messages, model, max_tokens):
    """
    Function to call the LLM model and return the response.
    :param messages: list of dictionaries with keys "role" and "content" with the role being one of "system", "user", or "assistant"
    :param model: the model name to use
    :param max_tokens: the maximum number of tokens to generate
    :return: the response from the model
    """
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        max_tokens=max_tokens
    )
    return chat_completion.choices[0].message.content

def convert_chat_to_llm_input(system_prompt, chat):
    # Convert the chat list of lists to the required format for the LLM
    messages = [ {"role": "system", "content": system_prompt}]
    for q, a in chat:
        messages.extend(
            [{"role": "user", "content": q}
                , {"role": "assistant", "content": a}]
        )
    return messages


################################################################################
# FUNCTION FOR TRANSLATING CODE
################################################################################

# this is called to actually send a request and receive response from the llm endpoint.

def llm_translate(system_prompt, input_code):
    messages = [
          {"role": "system", "content": system_prompt}
        , {"role": "user", "content": input_code}]

    # call the LLM end point.
    llm_answer = call_llm(
        messages=messages,
        model= os.environ["SERVED_MODEL_NAME"],
        max_tokens=int(os.environ["MAX_TOKENS"])
    )
    # Extract the code from in between the triple backticks (```), since LLM often prints the code like this.
    # Also removes the 'sql' prefix always added by the LLM.
    translation = llm_answer.split("Final answer:\n")[1].replace(">>", "").replace("<<", "")
    return translation


def llm_chat(system_prompt, query, chat_history):
    messages = convert_chat_to_llm_input(system_prompt, chat_history)
    messages.append({"role": "user", "content": query})
    # call the LLM end point.
    llm_answer = call_llm(
        messages=messages,
        model= os.environ["SERVED_MODEL_NAME"],
        max_tokens=int(os.environ["MAX_TOKENS"])
    )
    return llm_answer

def llm_intent(system_prompt, input_code):
    messages = [
          {"role": "system", "content": system_prompt}
        , {"role": "user", "content": input_code}]

    # call the LLM end point.
    llm_answer = call_llm(
        messages=messages,
        model= os.environ["SERVED_MODEL_NAME"],
        max_tokens=int(os.environ["MAX_TOKENS"])
    )
    return llm_answer


