from utils.configloader import Configloader
from app.sql_interface import SQLInterface

import os


def setup_UC_infra():
    # load config file into environment variables
    cl = Configloader()
    cl.read_yaml_to_env("../config.yaml")

    # get environment variables
    DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
    DATABRICKS_HOST = os.environ["DATABRICKS_HOST"]
    SQL_WAREHOUSE_HTTP_PATH = os.environ["SQL_WAREHOUSE_HTTP_PATH"]
    UC_CATALOG = os.environ["CATALOG"]
    UC_SCHEMA = os.environ["SCHEMA"]
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