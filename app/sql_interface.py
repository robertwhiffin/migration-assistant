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
