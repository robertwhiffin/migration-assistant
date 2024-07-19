from operator import itemgetter
import mlflow
from langchain_community.chat_models import ChatDatabricks

from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import HumanMessage, AIMessage

# ## Enable MLflow Tracing
mlflow.login()
mlflow.langchain.autolog()
############
# Helper functions
############
# Return the string contents of the most recent message from the user
def extract_user_query_string(chat_messages_array):
    return chat_messages_array[-1]["content"]

# Extract system prompt from the messages

def extract_system_prompt_string(chat_messages_array):
    return chat_messages_array[0]["content"]

# Return the chat history, which is is everything before the last question
def extract_chat_history(chat_messages_array):
    return chat_messages_array[1:-1]

#
# # Load the chain's configuration
# model_config = mlflow.models.ModelConfig(development_config="rag_chain_config.yaml")
#
# databricks_resources = model_config.get("databricks_resources")
# retriever_config = model_config.get("retriever_config")
# llm_config = model_config.get("llm_config")



############
# Required to:
# 1. Enable the RAG Studio Review App to properly display retrieved chunks
# 2. Enable evaluation suite to measure the retriever
############


############
# Prompt Template for generation
############
prompt = ChatPromptTemplate.from_messages(
    [
        (  # System prompt contains the instructions
            "system",
            "{system}",
        ),
        # If there is history, provide it.
        # Note: This chain does not compress the history, so very long converastions can overflow the context window.
        MessagesPlaceholder(variable_name="formatted_chat_history"),
        # User's most current question
        ("user", "{question}"),
    ]
)


# Format the converastion history to fit into the prompt template above.
def format_chat_history_for_prompt(chat_messages_array):
    history = extract_chat_history(chat_messages_array)
    formatted_chat_history = []
    if len(history) > 0:
        for chat_message in history:
            if chat_message["role"] == "user":
                formatted_chat_history.append(
                    HumanMessage(content=chat_message["content"])
                )
            elif chat_message["role"] == "assistant":
                formatted_chat_history.append(
                    AIMessage(content=chat_message["content"])
                )
    return formatted_chat_history


############
# FM for generation
############
model = ChatDatabricks(
    # endpoint="https://adb-984752964297111.11.azuredatabricks.net/serving-endpoints/databricks-meta-llama-3-70b-instruct/invocations",
    endpoint="databricks-meta-llama-3-70b-instruct"
    # extra_params=llm_config.get("llm_parameters"),
)

############
# RAG Chain
############
chain = (
    {
        "system": itemgetter("messages") | RunnableLambda(extract_system_prompt_string),
        "question": itemgetter("messages") | RunnableLambda(extract_user_query_string),
        "formatted_chat_history": itemgetter("messages") | RunnableLambda(format_chat_history_for_prompt),
    }
    | prompt
    | model
    | StrOutputParser()
)


mlflow.models.set_model(model=chain)
input_example = {
        "messages": [
            {
                "role": "system",
                "content": '''You are an AI assistant answer the questions''',
            },
            {
                "role": "ai",
                "content": 'codejam',
            },
            {
                "role": "user",
                "content": "what is the weatherl like in UK?",
            },
            {
                "role": "assistant",
                "content": "Good today",
            },
            {
                "role": "user",
                "content": "what was the previous question I asked?",
            },
        ]
    }

chain.invoke(input_example)

# Log the model to MLflow
# TODO: remove example_no_conversion once this papercut is fixed
experiment_name = "/Users/robert.whiffin@databricks.com/langchain-migration-app"
# mlflow.create_experiment(experiment_name)
mlflow.set_experiment(experiment_name)
with mlflow.start_run(run_name="test-chain",nested=True):
    # Tag to differentiate from the data pipeline runs
    mlflow.set_tag("type", "chain")

    logged_chain_info = mlflow.langchain.log_model(
        lc_model=chain
        ,artifact_path="chain"  # Required by MLflow
        ,input_example=  {"messages": [
                        {
                            "role": "System",
                            "content": "You are a helpful assistant",
                        },
                        {
                            "role": "user",
                            "content": "What is RAG?",
                        },
                    ]
                }
    )

mlflow.set_registry_uri('databricks-uc')

chain = mlflow.langchain.load_model(logged_chain_info.model_uri)
chain.invoke(
    {
        "messages": [
            {
                "role": "system",
                "content": '''You are an AI assistant answer the questions''',
            },
            {
                "role": "user",
                "content": "What is your name?",
            },
        ]
    }
)

import os
from utils.endpointclient import EndpointApiClient
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_registry_uri('databricks-uc')
client = MlflowClient()
UC_MODEL_NAME = "robert_whiffin.migration_assistant.chain"
catalog='robert_whiffin'
db='migration_assistant'
serving_endpoint_name ="rob-test-endpoint2"
uc_registered_model_info = mlflow.register_model(model_uri=logged_chain_info.model_uri, name=UC_MODEL_NAME, )
latest_model = client.get_model_version(UC_MODEL_NAME,3)

#TODO: use the sdk once model serving is available.
serving_client = EndpointApiClient()
# Start the endpoint using the REST API (you can do it using the UI directly)
auto_capture_config = {
    "catalog_name": catalog,
    "schema_name": db,
    "table_name_prefix": serving_endpoint_name
    }
environment_vars={
    "DATABRICKS_TOKEN": os.environ["DATABRICKS_TOKEN"]
    ,"DATABRICKS_HOST": os.environ["DATABRICKS_HOST"]
    ,"ENABLE_MLFLOW_TRACING": "true"
}
serving_client.create_endpoint_if_not_exists(
    serving_endpoint_name
    , model_name=UC_MODEL_NAME
    , model_version = latest_model.version
    , workload_size="Small"
    , scale_to_zero_enabled=True
    , wait_start = True
    , auto_capture_config=auto_capture_config
    , environment_vars=environment_vars
)

