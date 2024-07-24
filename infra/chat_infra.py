from operator import itemgetter
import mlflow
from mlflow.tracking import MlflowClient

import os

from utils.endpointclient import EndpointApiClient

from langchain_community.chat_models import ChatDatabricks
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import HumanMessage, AIMessage

def create_langchain_chat_model():
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

    # Return the chat history, which is everything before the last question
    def extract_chat_history(chat_messages_array):
        return chat_messages_array[1:-1]



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
    model = ChatDatabricks(endpoint=os.environ["SERVED_FOUNDATION_MODEL_NAME"])

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

    # Log the model to MLflow
    experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    try:
        mlflow.create_experiment(experiment_name)
        mlflow.set_experiment(experiment_name)
    except:
        mlflow.set_experiment(experiment_name)
    with mlflow.start_run():
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

    client = MlflowClient()

    catalog = os.environ.get("CATALOG")
    schema = os.environ.get("SCHEMA")
    UC_MODEL_NAME = os.environ.get("MLFLOW_MODEL_NAME")

    serving_endpoint_name ="project-gamma-endpoint"
    fully_qualified_name = f"{catalog}.{schema}.{UC_MODEL_NAME}"
    uc_registered_model_info = mlflow.register_model(model_uri=logged_chain_info.model_uri, name=fully_qualified_name)
    def get_latest_model_version(model_name):
      client = MlflowClient()
      model_version_infos = client.search_model_versions("name = '%s'" % model_name)
      return max([int(model_version_info.version) for model_version_info in model_version_infos]) or 1

    latest_version = get_latest_model_version(model_name=fully_qualified_name)
    latest_model = client.get_model_version(fully_qualified_name,latest_version)

    #TODO: use the sdk once model serving is available.
    serving_client = EndpointApiClient()
    # Start the endpoint using the REST API (you can do it using the UI directly)
    auto_capture_config = {
        "catalog_name": catalog,
        "schema_name": schema,
        "table_name_prefix": serving_endpoint_name
        }
    environment_vars={
        "DATABRICKS_TOKEN": os.environ.get("DATABRICKS_TOKEN")
        ,"DATABRICKS_HOST": os.environ.get("DATABRICKS_HOST")
        ,"ENABLE_MLFLOW_TRACING": "true"
    }
    serving_client.create_endpoint_if_not_exists(
        serving_endpoint_name
        , model_name=fully_qualified_name
        , model_version = latest_model.version
        , workload_size="Small"
        , scale_to_zero_enabled=True
        , wait_start = True
        , auto_capture_config=auto_capture_config
        , environment_vars=environment_vars
    )

