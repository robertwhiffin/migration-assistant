################################################################################
################################################################################
# takes in a dict of {table_name: str, columns: list} where the columns are the columns used from that table
# uses describe table to retrieve table and column descriptions from unity catalogue.
# wrapped in a try statement in case table not found in UC to make it work on code only
# look to do with system tables to do in one go
import os

from databricks import sql

class SQLInterface():

    def __init__(self, databricks_host, databricks_token, sql_warehouse_http_path):
        self.connection = sql.connect(
            server_hostname = databricks_host,
            http_path       = sql_warehouse_http_path,
            access_token    = databricks_token
        )
        self.cursor = self.connection.cursor()

    def execute_sql(self, cursor, sql):
        cursor.execute(sql)
        return cursor.fetchall()
