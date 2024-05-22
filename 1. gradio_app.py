import yaml
import gradio as gr
from openai import OpenAI
import os

import gradio as gr
from databricks import sql
from databricks.vector_search.client import VectorSearchClient
from utils.sqlglotfunctions import *


# # personal access token necessary for authenticating API requests. Stored using a secret
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
DATABRICKS_HOST = os.environ["DATABRICKS_HOST"]
# details on the vector store holding the similarity information
vsc = VectorSearchClient(
    workspace_url = "https://" + DATABRICKS_HOST
    ,personal_access_token = DATABRICKS_TOKEN
) # needto fix to use PAT and workspace url
VECTOR_SEARCH_ENDPOINT_NAME = os.environ["VECTOR_SEARCH_ENDPOINT_NAME"]
vs_index_fullname= os.environ["VS_INDEX_FULLNAME"]
intent_table = os.environ["INTENT_TABLE"]

# details for connecting to the llm endpoint

# the URL of the serving endpoint
MODEL_SERVING_ENDPOINT_URL = f"https://{DATABRICKS_HOST}serving-endpoints"

client = OpenAI(
  api_key=DATABRICKS_TOKEN,
  base_url=MODEL_SERVING_ENDPOINT_URL
)


# create a connection to the sql warehouse
connection = sql.connect(
server_hostname = DATABRICKS_HOST,
http_path       = os.environ["SQL_WAREHOUSE_HTTP_PATH"],
access_token    = DATABRICKS_TOKEN
)
cursor = connection.cursor()

# little helper function to make executing sql simpler.
def execute_sql(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchall()
    
################################################################################
################################################################################
# takes in a dict of {table_name: str, columns: list} where the columns are the columns used from that table
# uses describe table to retrieve table and column descriptions from unity catalogue. 
# wrapped in a try statement in case table not found in UC to make it work on code only
# look to do with system tables to do in one go
def get_table_metadata(input_dict):

    try:
        table_name = input_dict["table_name"]
        columns = input_dict["columns"]
        details = execute_sql(cursor, f"describe table extended {table_name}")
        table_comment = f"This is the information about the {table_name} table. " + list(filter(lambda x: x.col_name == "Comment", details)).pop().data_type
        row_details = execute_sql(cursor, f"describe table {table_name}")
        row_details = ["The column " + x.col_name + " has the comment \"" + x.comment + "\"" for x in details if x.col_name in columns]
        row_details = " ".join(row_details)
        return table_comment + " " + row_details
    except:
        return ''

################################################################################
################################################################################
# this is called to actually send a request and receive response from the llm endpoint.
def ask_llm(sql_query):
    # get tables and columns
    table_info = parse_sql(sql_query, 'tsql')
    # get table and column metadata
    table_metadata = []
    for x in table_info:
        table_details = get_table_metadata(x)
        if table_details != '':
            table_metadata.append(table_details)
    if table_metadata != []:
        # join up the metadata into a single string to add into the prompt
        table_column_descriptions = "\n\n ".join(table_metadata)
        # set the system prompt
        system_prompt = """
        Your job is to explain the intent of a SQL query. You are provided with the SQL Code and a summary of the information contained within the tables queried, and details about which columns are used from which table in the query. From the information about the tables and columns, you will infer what the query is intending to do.\n 
        """
        # build the query prompt by adding code and metadata descriptions
        query_prompt = f"This is the SQL code: {sql_query}. \n\n{table_column_descriptions}"
    else:
        system_prompt = """
        Your job is to explain the intent of a SQL query. You are provided with the SQL Code.
        """
        # build the query prompt by adding code and metadata descriptions
        query_prompt = f"This is the SQL code: {sql_query}"

    # call the LLM end point.
    chat_completion = client.chat.completions.create(
        messages=[
        {"role": "system", "content": system_prompt}
        ,{"role": "user",  "content": query_prompt}
        ],
        model=os.environ["SERVED_MODEL_NAME"],
        max_tokens=int(os.environ["MAX_TOKENS"])
    )
            
    #return [chat_completion.choices[0].message.content, query_prompt]
    return chat_completion.choices[0].message.content
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
def get_similar_code(intent):    
    results = vsc.get_index(VECTOR_SEARCH_ENDPOINT_NAME, vs_index_fullname).similarity_search(
    query_text=intent,
    columns=["code", "intent"],
    num_results=1)
    docs = results.get('result', {}).get('data_array', [])
    return(docs[0][0], docs[0][1])

################################################################################
################################################################################

# this is the app UI. it uses gradio blocks https://www.gradio.app/docs/gradio/blocks
# each gr.{} call adds a new element to UI, top to bottom. 
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # title with DfE image
    gr.Markdown("""<img align="right" src="https://asset.brandfetch.io/idSUrLOWbH/idm22kWNaH.png" alt="logo" width="120">

## A context aware migration assistant for explaining the intent of SQL code and converting from T-SQL to Spark SQL

#### This demo relies on the tables and columns referenced in the SQL query being present in Unity Catalogue and having their table comments and column comments populated. For the purpose of the demo, this was generated using the Databricks AI Generated Comments tool. 

""")
    # subheader
    gr.Markdown(""" ### Input your T-SQL code here for automatic translation to Spark-SQL and use AI to generate a statement of intent for the code's purpose.
                """)
    # input box for T-SQL code with nice formatting
    inp = gr.Code(
            label="Input T-SQL"
            ,language="sql-msSQL"
            )
    # a button labelled run
    btn = gr.Button("Run")
    # divider subheader
    gr.Markdown(""" ## Your Code Translated to Spark-SQL
                
                Translation is deterministic and done by SQL Glot
                """)
    # output box of the T-SQL translated to Spark SQL
    translated = gr.Code(
        label="Your code translated to Spark SQL"
        ,language="sql-sparkSQL"
        )
    # divider subheader
    gr.Markdown(""" ## AI generated intent of what your code aims to do. 
                
                Intent is determined by an LLM which uses the code and table & column metadata. 

                ***If the intent is incorrect, please edit***. Once you are happy that the description is correct, please click the button below to save the intent. This will help the Department by making it easier to identify duplication of what people are doing. 
                """)
    # a box to give the LLM generated intent of the code. This is editable as well. 
    explained = gr.Textbox(label="AI generated intent of your code.")

    # divider subheader
    gr.Markdown(""" ## Similar code 
                
                This code is thought to be similar to what you are doing, based on comparing the intent of your code with the intent of this code.
                """)    
    # a button
    find_similar_code=gr.Button("Find similar code")
    # a row with an code and text box to show the similar code
    with gr.Row():
        similar_code = gr.Code(
            label="Similar code to yours."
            ,language="sql-sparkSQL"
            )
        similar_intent = gr.Textbox(label="The similar codes intent.")

    # a button
    submit = gr.Button("Save code and intent")

    # assign actions to buttons when clicked.
    btn.click(fn=sqlglot_transpilation, inputs=inp, outputs=translated)
    btn.click(fn=ask_llm, inputs=inp, outputs=explained)
    find_similar_code.click(get_similar_code, inputs=explained, outputs=[similar_code, similar_intent])
    
    submit.click(save_intent, inputs=[inp, explained])

# this is necessary to get the app to run 
if __name__ == "__main__":
    demo.queue().launch(
    server_name=os.getenv("GRADIO_SERVER_NAME"), 
    server_port=int(os.getenv("GRADIO_SERVER_PORT")),
  )