################################################################################
################################################################################
# takes in a dict of {table_name: str, columns: list} where the columns are the columns used from that table
# uses describe table to retrieve table and column descriptions from unity catalogue.
# wrapped in a try statement in case table not found in UC to make it work on code only
# look to do with system tables to do in one go
import os

from databricks import sql
from utils.sqlglotfunctions import parse_sql

class SQLInterface():

    def __init__(self, databricks_host, databricks_token, sql_warehouse_http_path):
        self.connection = sql.connect(
            server_hostname = databricks_host,
            http_path       = sql_warehouse_http_path,
            access_token    = databricks_token
        )
        self.cursor = self.connection.cursor()

#     def _get_table_metadata(self, input_dict):
#
#         try:
#             table_name = input_dict["table_name"]
#             columns = input_dict["columns"]
#             details = self.execute_sql(self.cursor, f"describe table extended {table_name}")
#             table_comment = f"This is the information about the {table_name} table. " + list(filter(lambda x: x.col_name == "Comment", details)).pop().data_type
#             row_details = ["The column " + x.col_name + " has the comment \"" + x.comment + "\"" for x in details if x.col_name in columns]
#             row_details = " ".join(row_details)
#             return table_comment + " " + row_details
#         except:
#             return ''
#
# ################################################################################
# ################################################################################
# # use this to build to the initial prompt to get the intent
#
#     def build_table_metadata(self, sql_query):
#         # get tables and columns
#         table_info = parse_sql(sql_query, 'tsql')
#         # get table and column metadata
#         table_metadata = []
#         for x in table_info:
#             table_details = self._get_table_metadata(x)
#             if table_details != '':
#                 table_metadata.append(table_details)
#         if table_metadata != []:
#             # join up the metadata into a single string to add into the prompt
#             table_column_descriptions = "\n\n ".join(table_metadata)
#             return table_column_descriptions
#         else:
#             return None
#


    def execute_sql(self, cursor, sql):
        cursor.execute(sql)
        return cursor.fetchall()
