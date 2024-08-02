import os

from databricks.vector_search.client import VectorSearchClient

class SimilarCode():

    def __init__(self, databricks_token, databricks_host, vector_search_endpoint_name, vs_index_fullname, catalog, schema, intent_table):
        self.vsc = VectorSearchClient(
                workspace_url = databricks_host
                ,personal_access_token = databricks_token
            )
        self.vector_search_endpoint_name = vector_search_endpoint_name
        self.vs_index_fullname = f"{catalog}.{schema}.{vs_index_fullname}"
        self.intent_table = f"{catalog}.{schema}.{intent_table}"


    def save_intent(self, code, intent, cursor):
        code_hash = hash(code)

        cursor.execute(
            f"INSERT INTO {self.intent_table} VALUES ({code_hash}, \"{code}\", \"{intent}\")"
        )

    def get_similar_code(self, chat_history):
        intent=chat_history[-1][1]
        results = self.vsc.get_index(self.vector_search_endpoint_name, self.vs_index_fullname).similarity_search(
        query_text=intent,
        columns=["code", "intent"],
        num_results=1)
        docs = results.get('result', {}).get('data_array', [])
        return(docs[0][0], docs[0][1])


