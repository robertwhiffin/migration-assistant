import os

import gradio as gr

from app.llm import LLMCalls
from app.similar_code import SimilarCode
from app.sql_interface import SQLInterface
import logging  # For printing translation attempts in console (debugging)

# Setting up logger
logging.basicConfig
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# # personal access token necessary for authenticating API requests. Stored using a secret
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
DATABRICKS_HOST = os.environ["DATABRICKS_HOST"]
MODEL_NAME = os.environ["SERVED_MODEL_NAME"]
MAX_TOKENS = os.environ["MAX_TOKENS"]
SQL_WAREHOUSE_HTTP_PATH = os.environ["SQL_WAREHOUSE_HTTP_PATH"]
VECTOR_SEARCH_ENDPOINT_NAME = os.environ["VECTOR_SEARCH_ENDPOINT_NAME"]
VS_INDEX_FULLNAME = os.environ["VS_INDEX_FULLNAME"]
INTENT_TABLE = os.environ["INTENT_TABLE"]



sql_interface = SQLInterface(DATABRICKS_HOST, DATABRICKS_TOKEN, SQL_WAREHOUSE_HTTP_PATH)
translation_llm = LLMCalls(DATABRICKS_HOST, DATABRICKS_TOKEN,MODEL_NAME,MAX_TOKENS)
intent_llm = LLMCalls(DATABRICKS_HOST, DATABRICKS_TOKEN, MODEL_NAME, MAX_TOKENS)
similar_code_helper = SimilarCode(
      DATABRICKS_TOKEN
    , DATABRICKS_HOST
    , VECTOR_SEARCH_ENDPOINT_NAME
    , VS_INDEX_FULLNAME
    , INTENT_TABLE
)

################################################################################
################################################################################

# this is the app UI. it uses gradio blocks https://www.gradio.app/docs/gradio/blocks
# each gr.{} call adds a new element to UI, top to bottom. 
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # title with Databricks image
    gr.Markdown("""<img align="right" src="https://asset.brandfetch.io/idSUrLOWbH/idm22kWNaH.png" alt="logo" width="120">

## A migration assistant for explaining the intent of SQL code and conversion to Spark SQL

#### This demo relies on the tables and columns referenced in the SQL query being present in Unity Catalogue and having their table comments and column comments populated. For the purpose of the demo, this was generated using the Databricks AI Generated Comments tool. 

""")
    
################################################################################
#### TRANSLATION ADVANCED OPTIONS PANE
################################################################################
    with gr.Accordion(label="Translation Advanced Settings", open=False):
        with gr.Row():
            transation_system_prompt = gr.Textbox(
                label="Instructions for the LLM translation tool."
                ,value="""
                          You are an expert in multiple SQL dialects. You only reply with SQL code and with no other text. 
                          Your purpose is to translate the given SQL query to Databricks Spark SQL. 
                          You must follow these rules:
                          - You must keep all original catalog, schema, table, and field names.
                          - Convert all dates to dd-MMM-yyyy format using the date_format() function.
                          - Subqueries must end with a semicolon.
                          - Ensure queries do not have # or @ symbols.
                          - ONLY if the original query uses temporary tables (e.g. "INTO #temptable"), re-write these as either CREATE OR REPLACE TEMPORARY VIEW or CTEs. .
                          - Square brackets must be replaced with backticks.
                          - Custom field names should be surrounded by backticks. 
                          - Ensure queries do not have # or @ symbols.
                          - Only if the original query contains DECLARE and SET statements, re-write them according to the following format:
                                DECLARE VARIABLE variable TYPE DEFAULT value; For example: DECLARE VARIABLE number INT DEFAULT 9;
                                SET VAR variable = value; For example: SET VAR number = 9;
                          
                        Write an initial draft of the translated query. Then double check the output for common mistakes, including:
                        - Using NOT IN with NULL values
                        - Using UNION when UNION ALL should have been used
                        - Using BETWEEN for exclusive ranges
                        - Data type mismatch in predicates
                        - Properly quoting identifiers
                        - Using the correct number of arguments for functions
                        - Casting to the correct data type
                        - Using the proper columns for joins
                        
                        Use format:
                        
                        First draft: <<FIRST_DRAFT_QUERY>>
                        Final answer: <<FINAL_ANSWER_QUERY>>
                        """
                .strip()
                ,lines=40
            )

################################################################################
#### TRANSLATION PANE
################################################################################
    # subheader



    with gr.Accordion(label="Translation Pane", open=True):
        gr.Markdown(""" ### Input your T-SQL code here for automatic translation to Spark-SQL and use AI to generate a statement of intent for the code's purpose."""
                    )
        # hidden chat interface - to enable chatbot functionality
        translation_chat = gr.Chatbot(visible=False)
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
                # a button labelled translate
                translate_button = gr.Button("Translate")

            with gr.Column():
                # divider subheader
                gr.Markdown(""" ### Your Code Translated to Spark-SQL""")
                # output box of the T-SQL translated to Spark SQL
                translated = gr.Code(
                    label="Your code translated to Spark SQL"
                    ,language="sql-sparkSQL"
                    )
                translation_prompt = gr.Textbox(
                    label = "Adjustments for translation"
                )

        def translate_respond(system_prompt, message, chat_history):
            bot_message = translation_llm.llm_chat(system_prompt, message, chat_history)
            chat_history.append([message, bot_message])
            return chat_history, chat_history[-1][1]


        # helper function to take the output from llm_translate and return outputs for chatbox and textbox
        # chatbox input is a list of lists, each list is a message from the user and the response from the LLM
        # textbox input is a string
        def llm_translate_wrapper(system_prompt, input_code):
            # call the LLM to translate the code
            translated_code = translation_llm.llm_translate(system_prompt, input_code)
            # wrap the translated code in a list of lists for the chatbot
            chat_history = [[input_code, translated_code]]
            return chat_history, translated_code

        # reset hidden chat history and prompt
        translate_button.click(
            fn=lambda: ([['', '']], '')
            ,inputs=None
            ,outputs=[translation_chat, translation_prompt]
        )
        # do translation
        translate_button.click(
              fn=llm_translate_wrapper
            , inputs=[transation_system_prompt, input_code]
            , outputs=[translation_chat, translated]
        )
        # refine translation
        translation_prompt.submit(
            fn=translate_respond
            , inputs=[transation_system_prompt, translation_prompt, translation_chat]
            , outputs=[translation_chat, translated]

        )

################################################################################
#### AI GENERATED INTENT PANE
################################################################################
    # divider subheader
    with gr.Accordion(label="Advanced Intent Settings", open=False):
        gr.Markdown(""" ### Advanced settings for the generating the intent of the input code.""")
        with gr.Row():
            intent_system_prompt = gr.Textbox(
                label="System prompt of the LLM to generate the intent. Editing will reset the intent."
                , value="""Your job is to explain intent of the provided SQL code.
                        """
                .strip()
            )
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


        def intent_respond(system_prompt, message, chat_history):
            bot_message = intent_llm.llm_chat(system_prompt, message, chat_history)
            chat_history.append([message, bot_message])
            return chat_history, '', bot_message

        def llm_chat_wrapper(system_prompt, input_code):
            # call the LLM to translate the code
            intent = intent_llm.llm_intent(system_prompt, input_code)
            # wrap the translated code in a list of lists for the chatbot
            chat_history = [[input_code, intent]]
            return chat_history, '', intent

        explain_button.click(
            fn=llm_chat_wrapper
            , inputs=[
                intent_system_prompt
                , input_code
                ]
            , outputs=[chatbot, msg, explained]
            )
        msg.submit(
            fn=intent_respond
            ,inputs = [
                intent_system_prompt
                , msg
                , chatbot
                ],
            outputs= [chatbot, msg, explained])
        clear.click(lambda : None, None, chatbot, queue=False)




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
        fn= similar_code_helper.get_similar_code
        , inputs=chatbot
        , outputs=[similar_code, similar_intent])

    def save_intent_wrapper(input_code, explained):
        gr.Info("Saving intent")
        similar_code_helper.save_intent(input_code, explained, sql_interface.cursor)
        gr.Info("Intent saved")

    submit.click(
        save_intent_wrapper
        , inputs=[input_code, explained]
    )


# for local dev
try:
    if os.environ["LOCALE"] =="local_dev":
        demo.queue().launch()
except KeyError:
    pass

# this is necessary to get the app to run on databricks
if __name__ == "__main__":
    demo.queue().launch(
    server_name=os.getenv("GRADIO_SERVER_NAME"), 
    server_port=int(os.getenv("GRADIO_SERVER_PORT")),
  )
