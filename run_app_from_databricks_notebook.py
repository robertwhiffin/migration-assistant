# Databricks notebook source
#pip install -r "requirements.txt"

# COMMAND ----------

#dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %load_ext autoreload
# MAGIC %autoreload 2

# COMMAND ----------

from utils.configloader import ConfigLoader
cl = ConfigLoader()
cl.read_yaml_to_env("config.yaml")

# COMMAND ----------

from dbtunnel import dbtunnel
dbtunnel.kill_port(8080)
app='././gradio_app.py'
dbtunnel.gradio(path=app).run()
