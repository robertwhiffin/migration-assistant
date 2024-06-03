# Databricks notebook source
pip install openai sqlglot openpyxl dbtunnel[asgiproxy,gradio] databricks-vectorsearch==0.35 fastapi nest_asyncio uvicorn

# COMMAND ----------

pip install -U gradio==4.27.0 databricks-sdk databricks-sql-connector

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

from utils.configloader import configLoader
cl = configLoader() 
cl.read_yaml_to_env("config.yaml")

# COMMAND ----------

from dbtunnel import dbtunnel
dbtunnel.kill_port(8080)
app='././1. gradio_app.py'
dbtunnel.gradio(path=app).run()
