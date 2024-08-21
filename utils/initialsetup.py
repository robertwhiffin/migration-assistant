from databricks.sdk import WorkspaceClient
from infra.sql_warehouse_infra import SqlWarehouseInfra
from infra.unity_catalog_infra import UnityCatalogInfra
from infra.vector_search_infra import VectorSearchInfra
from infra.chat_infra import ChatInfra
from infra.secrets_infra import SecretsInfra
from infra.app_serving_cluster_infra import AppServingClusterInfra

import logging
import os
from utils.upload_files_to_workspace import FileUploader
import yaml
w = WorkspaceClient(product="sql_migration_assistant", product_version="0.0.1")
def setup_migration_assistant(w):

    logging.info("Setting up infrastructure")
    # create empty config dict to fill in
    config = {}
    logging.info("Choose or create cluster to host review app")
    app_cluster_infra = AppServingClusterInfra(config, w)
    app_cluster_infra.choose_serving_cluster()
    config = app_cluster_infra.config

    logging.info("***Choose a Databricks SQL Warehouse***")
    sql_infra = SqlWarehouseInfra(config, w)
    sql_infra.choose_compute()
    config = sql_infra.config

    logging.info("Setting up Unity Catalog infrastructure")
    uc_infra = UnityCatalogInfra(config, w)
    uc_infra.choose_UC_catalog()
    uc_infra.choose_schema_name()
    uc_infra.create_code_intent_table()
    config= uc_infra.config
    logging.info("Setting up Vector Search infrastructure")
    vs_infra = VectorSearchInfra(config, w)
    vs_infra.choose_VS_endpoint()
    vs_infra.choose_embedding_model()
    vs_infra.create_VS_index()
    logging.info("Setting up Chat infrastructure")
    chat_infra = ChatInfra(config, w)
    chat_infra.setup_foundation_model_infra()
    config=chat_infra.config
    logging.info("Setting up secrets")
    secrets_infra = SecretsInfra(config, w)
    secrets_infra.create_secret_PAT()
    return secrets_infra.config

final_config = setup_migration_assistant()

with open("config.yaml", 'w') as file:
    yaml.dump(final_config, file)

uploader = FileUploader(w)
files_to_upload = [
    "config.yaml",
    "utils/runindatabricks.py",
    "gradio_app.py",
    "run_app_from_databricks_notebook.py",
    "utils/configloader.py",
]
files_to_upload.extend([f"app/{x}" for x in os.listdir("app") if x[-3:] == ".py"])
for f in files_to_upload:
    uploader.upload(f)

