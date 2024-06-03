import os

from databricks.vector_search.client import VectorSearchClient

from app.table_metadata import cursor
# details on the vector store holding the similarity information
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
DATABRICKS_HOST = os.environ["DATABRICKS_HOST"]

vsc = VectorSearchClient(
    workspace_url = "https://" + DATABRICKS_HOST
    ,personal_access_token = DATABRICKS_TOKEN
)
VECTOR_SEARCH_ENDPOINT_NAME = os.environ["VECTOR_SEARCH_ENDPOINT_NAME"]
vs_index_fullname= os.environ["VS_INDEX_FULLNAME"]
intent_table = os.environ["INTENT_TABLE"]

################################################################################
################################################################################
# this writes the code & intent into the lookup table
def save_intent(code, intent):
    code_hash = hash(code)

    cursor.execute(
        f"INSERT INTO {intent_table} VALUES ({code_hash}, \"{code}\", \"{intent}\")"
    )

################################################################################
################################################################################
# this does a look up on the vector store to find the most similar code based on the intent
def get_similar_code(chat_history):
    intent=chat_history[-1][1]
    results = vsc.get_index(VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname).similarity_search(
    query_text=intent,
    columns=["code", "intent"],
    num_results=1)
    docs = results.get('result', {}).get('data_array', [])
    return(docs[0][0], docs[0][1])

