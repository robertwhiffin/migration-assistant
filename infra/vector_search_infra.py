from infra.unity_catalog_infra import setup_UC_infra
from app.sql_interface import SQLInterface

import os
from databricks.vector_search.client import VectorSearchClient

def setup_VS_infra():

    # get environment variables
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
    SQL_WAREHOUSE_HTTP_PATH = os.environ.get("SQL_WAREHOUSE_HTTP_PATH")
    UC_CATALOG = os.environ.get("CATALOG")
    UC_SCHEMA = os.environ.get("SCHEMA")
    VECTOR_SEARCH_ENDPOINT_NAME = os.environ.get("VECTOR_SEARCH_ENDPOINT_NAME")
    VS_INDEX_FULLNAME = os.environ.get("VS_INDEX_FULLNAME")
    VS_INTENT_TABLE = os.environ.get("VS_INTENT_TABLE")
    EMBEDDING_MODEL_ENDPOINT = os.environ.get("EMBEDDING_MODEL_ENDPOINT")
    sql_interface = SQLInterface(DATABRICKS_HOST, DATABRICKS_TOKEN, SQL_WAREHOUSE_HTTP_PATH)

    # do UC setup if not done
    setup_UC_infra()

    # create table to store code and intent if doesn't exist
    sql_interface.execute_sql(
        sql_interface.cursor
        , f"CREATE TABLE IF NOT EXISTS `{UC_CATALOG}`.`{UC_SCHEMA}`.`{VS_INTENT_TABLE}` (id BIGINT, code STRING, intent STRING) TBLPROPERTIES (delta.enableChangeDataFeed = true)"
    )

    client = VectorSearchClient()


    # create vector search endpoint if doesn't exist.
    try:
        # if endpoint exists, do nothing
        client.get_endpoint(VECTOR_SEARCH_ENDPOINT_NAME)
    except Exception as e:
        # if endpoint doesn't exist, create it
        if '"error_code":"NOT_FOUND"' in str(e):
            try:
                client.create_endpoint_and_wait(
                    name=VECTOR_SEARCH_ENDPOINT_NAME
                    ,endpoint_type="STANDARD"
                    ,verbose=True
                )
            # if get a different error, raise it
            except Exception as e:
                raise e
        else:
            pass

    # if index exists, do nothing
    try:
        client.get_index(VECTOR_SEARCH_ENDPOINT_NAME, f"{UC_CATALOG}.{UC_SCHEMA}.{VS_INDEX_FULLNAME}")
    except Exception as e:
        # if index doesn't exist, create it
        if '"error_code":"RESOURCE_DOES_NOT_EXIST"' in str(e):
            try:
                client.create_delta_sync_index(
                    endpoint_name=VECTOR_SEARCH_ENDPOINT_NAME
                    ,index_name=f"{UC_CATALOG}.{UC_SCHEMA}.{VS_INDEX_FULLNAME}"
                    ,source_table_name=f"{UC_CATALOG}.{UC_SCHEMA}.{VS_INTENT_TABLE}"
                    ,pipeline_type='TRIGGERED'
                    ,primary_key="id"
                    ,embedding_source_column="code"
                    ,embedding_model_endpoint_name=EMBEDDING_MODEL_ENDPOINT
                )
            # if get a different error, raise it
            except Exception as e:
                raise e
        else:
            pass


