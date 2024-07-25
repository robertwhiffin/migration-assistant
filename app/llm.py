#from openai import OpenAI
import os
from langchain_community.chat_models import ChatDatabricks
class LLMCalls():
    def __init__(self, databricks_host, databricks_token, model_name, max_tokens):
        # self.MODEL_SERVING_ENDPOINT_URL = f"https://{databricks_host}/serving-endpoints"
        # self.client = OpenAI(
        #     api_key=databricks_token,
        #     base_url=self.MODEL_SERVING_ENDPOINT_URL
        # )
        # self.model_name = model_name
        # self.max_tokens = int(max_tokens)
        self.model = ChatDatabricks(endpoint=os.environ.get("LANGCHAIN_SERVING_ENDPOINT_NAME"))


    def call_llm(self, messages):
        """
        Function to call the LLM model and return the response.
        :param messages: list of dictionaries with keys "role" and "content" with the role being one of "system", "user", or "assistant"
        :param model: the model name to use
        :param max_tokens: the maximum number of tokens to generate
        :return: the response from the model
        """
        return self.model.invoke(messages).content
        # chat_completion = self.client.chat.completions.create(
        #     messages=messages,
        #     model=self.model_name,
        #     max_tokens=self.max_tokens
        # )
        # return chat_completion.choices[0].message.content



    def convert_chat_to_llm_input(self, system_prompt, chat):
        # Convert the chat list of lists to the required format for the LLM
        messages = [ {"role": "system", "content": system_prompt}]
        for q, a in chat:
            messages.extend(
                [{"role": "user", "content": q}
                    , {"role": "assistant", "content": a}]
            )
        return messages


    ################################################################################
    # FUNCTION FOR TRANSLATING CODE
    ################################################################################

    # this is called to actually send a request and receive response from the llm endpoint.

    def llm_translate(self, system_prompt, input_code):
        messages = [
              {"role": "system", "content": system_prompt}
            , {"role": "user", "content": input_code}]

        # call the LLM end point.
        llm_answer = self.call_llm(
            messages=messages
        )
        # Extract the code from in between the triple backticks (```), since LLM often prints the code like this.
        # Also removes the 'sql' prefix always added by the LLM.
        translation = llm_answer.split("Final answer:\n")[1].replace(">>", "").replace("<<", "")
        return translation


    def llm_chat(self, system_prompt, query, chat_history):
        messages = self.convert_chat_to_llm_input(system_prompt, chat_history)
        messages.append({"role": "user", "content": query})
        # call the LLM end point.
        llm_answer = self.call_llm(
            messages=messages
        )
        return llm_answer

    def llm_intent(self, system_prompt, input_code):
        messages = [
              {"role": "system", "content": system_prompt}
            , {"role": "user", "content": input_code}]

        # call the LLM end point.
        llm_answer = self.call_llm(
            messages=messages
        )
        return llm_answer


