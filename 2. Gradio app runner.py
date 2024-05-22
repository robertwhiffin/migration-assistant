# Databricks notebook source
pip install openai sqlglot openpyxl dbtunnel[asgiproxy,gradio] databricks-vectorsearch==0.35

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

# COMMAND ----------

# DBTITLE 1,Sample SQL query to test

"""

SELECT
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
  c.[country_name]


"""

# COMMAND ----------

# DBTITLE 1,Sample SQL query to test
"""

SELECT
  c.country_name,
  AVG(d.num_dependents) AS avg_dependents,
  AVG(e.salary) AS avg_salary
FROM
  (
    SELECT
      employee_id,
      COUNT(dependent_id) AS num_dependents
    FROM
      robert_whiffin.dfe_code_assistant.dependents
    GROUP BY
      employee_id
  ) d
  RIGHT JOIN robert_whiffin.dfe_code_assistant.employees e ON d.employee_id = e.employee_id
  JOIN robert_whiffin.dfe_code_assistant.departments dep ON e.department_id = dep.department_id
  JOIN robert_whiffin.dfe_code_assistant.locations l ON dep.location_id = l.location_id
  JOIN robert_whiffin.dfe_code_assistant.countries c ON l.country_id = c.country_id
GROUP BY
  c.country_name
ORDER BY
  c.country_name

"""

# COMMAND ----------

# DBTITLE 1,Sample SQL query to test
"""
with average_salarys as (
  SELECT
    d.department_id,
    avg(salary) as average_salary
  FROM robert_whiffin.dfe_code_assistant.employees e
  inner join robert_whiffin.dfe_code_assistant.departments d on e.department_id = d.department_id
  group by d.department_id
)

select 
  first_name
  ,last_name
  ,salary
  ,average_salary 
  ,department_name
from robert_whiffin.dfe_code_assistant.employees e
inner join average_salarys a on e.department_id = a.department_id
inner join robert_whiffin.dfe_code_assistant.departments d on e.department_id = d.department_id
where salary > a.average_salary
"""
