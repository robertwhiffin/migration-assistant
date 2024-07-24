
# TODO finish this

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
scope='fieldeng'
key='rgwhiffin'
# create scope if note exists
if not w.secrets.get_scope(scope):
    w.secrets.create_scope(scope)


w.secrets.put_secret(scope=scope, key=key, string_value=pat)