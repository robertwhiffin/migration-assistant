# Databricks notebook source
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs, workspace

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

scopes = w.secrets.list_scopes()
scopes

# COMMAND ----------

w = WorkspaceClient()

a_job = list(w.jobs.list())[1]

# COMMAND ----------

scheduled_jobs = []
for job in w.jobs.list(expand_tasks=True):
  if job.settings.schedule:
    scheduled_jobs.append(job)

# COMMAND ----------

scheduled_jobs[1].settings.tasks[0]

# COMMAND ----------

def is_sql_notebook(path_object):
  return path_object.language == workspace.Language.SQL

sql_notebooks = list(filter(is_sql_notebook, objects))
a_sql_notebook = sql_notebooks[1]

# COMMAND ----------


with w.workspace.download(a_sql_notebook.path) as f:
    content = f.read()
content
