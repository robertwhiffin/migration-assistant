from databricks.sdk import WorkspaceClient

class SimilarCode():

    def __init__(self, config):
        self.w = WorkspaceClient()
        self.config = config

        self.migration_assistant_UC_catalog = self.config.get("CATALOG")
        self.migration_assistant_UC_schema = self.config.get("SCHEMA")

        self.migration_assistant_VS_table = self.config.get('CODE_INTENT_TABLE_NAME')
        self.migration_assistant_VS_index = self.config.get('VS_INDEX_NAME')
        self.default_VS_endpoint_name = self.config.get("VECTOR_SEARCH_ENDPOINT_NAME")

        self.warehouseID = self.config.get('DEFAULT_SQL_WAREHOUSE_ID')
    def save_intent(self, code, intent, cursor):
        code_hash = hash(code)

        _ = self.w.statement_execution.execute_statement(
            warehouse_id=self.warehouseID,
            catalog=self.migration_assistant_UC_catalog,
            schema=self.migration_assistant_UC_schema,
            statement=f"INSERT INTO {self.migration_assistant_VS_table} VALUES ({code_hash}, \"{code}\", \"{intent}\")"
        )

    def get_similar_code(self, chat_history):
        intent=chat_history[-1][1]
        results = self.w.vector_search_indexes.query_index(
            index_name=self.migration_assistant_VS_index,
            columns=["code", "intent"],
            query_text=intent,
            num_results=1
        )
        docs = results.result.data_array
        return(docs[0][0], docs[0][1])



