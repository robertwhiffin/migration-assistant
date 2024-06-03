import os

import gradio as gr

from app.llm import ask_llm, call_llm_for_chat
from app.similar_code import save_intent, get_similar_code
from utils.sqlglotfunctions import *


# # personal access token necessary for authenticating API requests. Stored using a secret
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
DATABRICKS_HOST = os.environ["DATABRICKS_HOST"]

# needto fix to use PAT and workspace url

# TODO
'''
- Remove table generated metadata incorporation
- add in advanced section for intent generation seperate to translation
- add in prompt in advanced translaton section
- add in LLM cycle for translation with prompt interface

'''


################################################################################
################################################################################

# this is the app UI. it uses gradio blocks https://www.gradio.app/docs/gradio/blocks
# each gr.{} call adds a new element to UI, top to bottom. 
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # title with Databricks image
    gr.Markdown("""<img align="right" src="https://asset.brandfetch.io/idSUrLOWbH/idm22kWNaH.png" alt="logo" width="120">

## A context aware migration assistant for explaining the intent of SQL code and conversion to Spark SQL

#### This demo relies on the tables and columns referenced in the SQL query being present in Unity Catalogue and having their table comments and column comments populated. For the purpose of the demo, this was generated using the Databricks AI Generated Comments tool. 

""")
    
################################################################################
#### ADVANCED OPTIONS PANE
################################################################################
    with gr.Accordion(label="Advanced Settings", open=False):
        with gr.Row():
            # select SQL flavour
            sql_flavour = gr.Dropdown(
                label = "Input SQL Type. Select SQL if unknown."
                ,choices = [
                     ("SQL", 'sql')
                    ,("Transact SQL", 'sql-msSQL')
                    ,("MYSQL"       , 'sql-mySQL')
                    ,("SQLITE"      , 'sql-sqlite')
                    ,("PL/SQL"      , 'sql-plSQL')
                    ,("HiveQL"      , 'sql-hive')
                    ,("PostgreSQL"  , 'sql-pgSQL')
                    ,("Spark SQL"   , 'sql-sparkSQL')
                    ]
                ,value="sql"
            )
            # this function updates the code formatting box to use the selected sql flavour
            def update_input_code_box(language):
                input_code = gr.Code(
                    label="Input SQL"
                    ,language=language
                    )
                return input_code
            
            # select whether to use table metadata
            use_table_metadata = gr.Checkbox(
                label="Use table metadata if available"
                ,value=True
            )
        llm_sys_prompt_metadata = gr.Textbox(
            label="System prompt for LLM to generate code intent if table metadata present."
            ,value="""
                Your job is to explain the intent of a SQL query. You are provided with the SQL Code and a summary of the information contained within the tables queried, and details about which columns are used from which table in the query. From the information about the tables and columns, you will infer what the query is intending to do.
                """.strip()
            )
        llm_sys_prompt_no_metadata = gr.Textbox(
            label="System prompt for LLM to generate code intent if table metadata absent."
            ,value="""
                Your job is to explain the intent of this SQL code.
                """.strip()
            )
################################################################################
#### TRANSLATION PANE
################################################################################
    # subheader
    with gr.Accordion(label="Translation Pane", open=True):
        gr.Markdown(""" ### Input your T-SQL code here for automatic translation to Spark-SQL and use AI to generate a statement of intent for the code's purpose."""
                    )

        # a button labelled translate
        translate_button = gr.Button("Translate") 
        with gr.Row():

            with gr.Column():
                gr.Markdown(
                    """ ### Input your T-SQL code here for translation to Spark-SQL."""
                    )
                
                # input box for SQL code with nice formatting
                input_code = gr.Code(
                        label="Input SQL"
                        ,language='sql-msSQL'
                        ,value="""SELECT
  c.[country_name],
  AVG([dep_count]) AS average_dependents
FROM
  (
    SELECT
      e.[employee_id]
      ,e.[department_id]
      ,COUNT(d.[dependent_id]) AS dep_count
    FROM
      [robert_whiffin].[dfe_code_assistant].[employees] e
      LEFT JOIN [robert_whiffin].[dfe_code_assistant].[dependents] d ON e.[employee_id] = d.[employee_id]
    GROUP BY
      e.[employee_id]
      ,e.[department_id]
  ) AS subquery
  JOIN [robert_whiffin].[dfe_code_assistant].[departments] dep ON subquery.[department_id] = dep.[department_id]
  JOIN [robert_whiffin].[dfe_code_assistant].[locations] l ON dep.[location_id] = l.[location_id]
  JOIN [robert_whiffin].[dfe_code_assistant].[countries] c ON l.[country_id] = c.[country_id]
GROUP BY
  c.[country_name]
ORDER BY
  c.[country_name]"""
                        )
            # the input code box gets updated when a user changes a setting in the Advanced section
                sql_flavour.input(update_input_code_box, sql_flavour, input_code)
            
            with gr.Column():
                # divider subheader
                gr.Markdown(""" ### Your Code Translated to Spark-SQL""")
                # output box of the T-SQL translated to Spark SQL
                translated = gr.Code(
                    label="Your code translated to Spark SQL"
                    ,language="sql-sparkSQL"
                    )
        translate_button.click(fn=sqlglot_transpilation, inputs=input_code, outputs=translated)

################################################################################
#### AI GENERATED INTENT PANE
################################################################################
    # divider subheader

    with gr.Accordion(label="Intent Pane", open=True):
        gr.Markdown(""" ## AI generated intent of what your code aims to do. 
                    
                    Intent is determined by an LLM which uses the code and table & column metadata. 

                    ***If the intent is incorrect, please edit***. Once you are happy that the description is correct, please click the button below to save the intent. This will help the Department by making it easier to identify duplication of what people are doing. 
                    """)
        # a box to give the LLM generated intent of the code. This is editable as well. 
        explain_button = gr.Button("Explain code intent using AI.")
        explained = gr.Textbox(label="AI generated intent of your code.", visible=False)

        chatbot = gr.Chatbot(
            label = "AI Chatbot for Intent Extraction"
            ,height="70%"
            )
        
        msg = gr.Textbox(label="Instruction")
        clear = gr.ClearButton([msg, chatbot])

        def user(user_message, history):
            return "", history + [[user_message, None]]

        def respond(chat_history, message, metadata_prompt, no_metadata_prompt, sql_query ):                
            bot_message = call_llm_for_chat(chat_history, message, metadata_prompt, no_metadata_prompt, sql_query)
            chat_history.append([message, bot_message])
            return "", chat_history
        
        explain_button.click(
            fn=ask_llm
            , inputs=[
                llm_sys_prompt_metadata
                , llm_sys_prompt_no_metadata
                , input_code
                ]
            , outputs=[msg, chatbot]
            )
        # msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        #     respond, chatbot, chatbot
        # )
        msg.submit(
            fn=respond
            ,inputs = [
                chatbot
                , msg
                , llm_sys_prompt_metadata
                , llm_sys_prompt_no_metadata
                , input_code
                ],
            outputs= [msg, chatbot])
        clear.click(lambda: None, None, chatbot, queue=False)




################################################################################
#### SIMILAR CODE PANE
################################################################################
    # divider subheader

    with gr.Accordion(label="Similar Code Pane", open=True):
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
    find_similar_code.click(
        fn=get_similar_code
        , inputs=chatbot
        , outputs=[similar_code, similar_intent])
    
    submit.click(save_intent, inputs=[input_code, explained])


# for local dev
if os.environ["LOCALE"] =="local_dev":
    demo.queue().launch()

# this is necessary to get the app to run on databricks
if __name__ == "__main__":
    demo.queue().launch(
    server_name=os.getenv("GRADIO_SERVER_NAME"), 
    server_port=int(os.getenv("GRADIO_SERVER_PORT")),
  )
