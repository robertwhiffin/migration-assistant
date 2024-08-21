'''
This code is called after the user has run through the configutation steps in initialsetup.py.
This uploads the config.yaml, runindatabricks.py, and gradio_app.py files to the Databricks workspace.
'''

from databricks.labs.blueprint.installation import Installation
from databricks.sdk import WorkspaceClient
import os
class FileUploader():
    def __init__(self):
        self.w = WorkspaceClient()
        self.installer = Installation(self.w, "sql_migration_assistant")

    def upload(self, file_name, ):
        with open(file_name, 'rb') as file:
            contents = file.read()
            self.installer.upload(file_name, contents)





uploader = FileUploader()
files_to_upload = [
    "config.yaml",
    "utils/runindatabricks.py",
    "gradio_app.py",
    "run_app_from_databricks_notebook.py",
    "utils/configloader.py",
]
files_to_upload.extend([f"app/{x}" for x in os.listdir("app") if x[-3:] == ".py"])
for f in files_to_upload:
    uploader.upload(f)