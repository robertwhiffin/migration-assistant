from utils.configloader import ConfigLoader
    #load config file into environment variables
cl = ConfigLoader()
cl.read_yaml_to_env("config.yaml")

from infra.chat_infra import setup_chat_infra
from infra.unity_catalog_infra import setup_UC_infra
from infra.vector_search_infra import setup_VS_infra

def setup_gamma():
    print("Setting up Gamma infrastructure")
    print("Setting up Unity Catalog infrastructure")
    setup_UC_infra()
    print("Setting up Vector Search infrastructure")
    setup_VS_infra()
    print("Setting up Chat infrastructure")
    setup_chat_infra()