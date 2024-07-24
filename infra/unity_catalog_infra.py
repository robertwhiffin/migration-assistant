from app.sql_interface import SQLInterface

import os


def setup_UC_infra():

    # get environment variables
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")
    DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
    SQL_WAREHOUSE_HTTP_PATH = os.environ.get("SQL_WAREHOUSE_HTTP_PATH")
    UC_CATALOG = os.environ.get("CATALOG")
    UC_SCHEMA = os.environ.get("SCHEMA")
    sql_interface = SQLInterface(DATABRICKS_HOST, DATABRICKS_TOKEN, SQL_WAREHOUSE_HTTP_PATH)

    # create catalog and schema if not exist
    sql_interface.execute_sql(
        sql_interface.cursor
        , f"CREATE CATALOG IF NOT EXISTS `{UC_CATALOG}`"
    )
    sql_interface.execute_sql(
        sql_interface.cursor
        , f"CREATE SCHEMA IF NOT EXISTS `{UC_CATALOG}`.`{UC_SCHEMA}`"
    )