from infra.sql_warehouse_infra import SqlWarehouseInfra
from infra.unity_catalog_infra import UnityCatalogInfra
from infra.vector_search_infra import VectorSearchInfra
from infra.chat_infra import ChatInfra
import logging
import yaml

def setup_migration_assistant():
    logging.info("Setting up infrastructure")
    # load config file
    with open("template_config.yaml", 'r') as file:
        config = yaml.safe_load(file)
    logging.info("***Choose a Databricks SQL Warehouse***")
    sql_infra = SqlWarehouseInfra(config)
    sql_infra.choose_compute()
    config = sql_infra.config
    logging.info("Setting up Unity Catalog infrastructure")
    uc_infra = UnityCatalogInfra(config)
    uc_infra.choose_UC_catalog()
    uc_infra.choose_schema_name()
    uc_infra.create_code_intent_table()
    config= uc_infra.config
    logging.info("Setting up Vector Search infrastructure")
    vs_infra = VectorSearchInfra(config)
    vs_infra.choose_VS_endpoint()
    vs_infra.choose_embedding_model()
    vs_infra.create_VS_index()
    logging.info("Setting up Chat infrastructure")
    chat_infra = ChatInfra(config)
    chat_infra.setup_foundation_model_infra()
    return chat_infra.config

final_config = setup_migration_assistant()

with open("config.yaml", 'w') as file:
    yaml.dump(final_config, file)
