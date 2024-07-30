# Databricks notebook source
pip install -r "requirements.txt"

# COMMAND ----------
pip install dbtunnel==0.14.6

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

from utils.initialsetup import setup_gamma
from utils.runindatabricks import run_app
setup_gamma()
run_app()