from utils.configloader import ConfigLoader
    #load config file into environment variables
cl = ConfigLoader()
cl.read_yaml_to_env("config.yaml")

from infra.chat_infra import setup_chat_infra,create_langchain_chat_model
from infra.unity_catalog_infra import setup_UC_infra
from infra.vector_search_infra import setup_VS_infra

def setup_gamma():
    print("Setting up Gamma infrastructure")
    print("Setting up Unity Catalog infrastructure")
    setup_UC_infra()
    print("Setting up Vector Search infrastructure")
    setup_VS_infra()
    # Create the model if it doesn't exist
    print("Creating Langchain Chat model if not exists.")
    create_langchain_chat_model()
    print("Setting up Chat infrastructure")
    setup_chat_infra()