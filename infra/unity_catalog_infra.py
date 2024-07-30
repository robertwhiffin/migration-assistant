from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound, PermissionDenied

import os

def setup_UC_infra():

    # get environment variables
    UC_CATALOG = os.environ.get("CATALOG")
    UC_SCHEMA = os.environ.get("SCHEMA")

    w = WorkspaceClient()

    # Create UC Catalog if it does not exist, otherwise, raise an exception
    try:
        _ = w.catalogs.get(UC_CATALOG)
        print(f"PASS: UC catalog `{UC_CATALOG}` exists")
    except NotFound as e:
        print(f"`{UC_CATALOG}` does not exist, trying to create...")
        try:
            _ = w.catalogs.create(name=UC_CATALOG)
        except PermissionDenied as e:
            print(
                f"FAIL: `{UC_CATALOG}` does not exist, and no permissions to create.  Please provide an existing UC Catalog.")
            raise ValueError(f"Unity Catalog `{UC_CATALOG}` does not exist.")

    # Create UC Schema if it does not exist, otherwise, raise an exception
    try:
        _ = w.schemas.get(full_name=f"{UC_CATALOG}.{UC_SCHEMA}")
        print(f"PASS: UC schema `{UC_CATALOG}.{UC_SCHEMA}` exists")
    except NotFound as e:
        print(f"`{UC_CATALOG}.{UC_SCHEMA}` does not exist, trying to create...")
        try:
            _ = w.schemas.create(name=UC_SCHEMA, catalog_name=UC_CATALOG)
            print(f"PASS: UC schema `{UC_CATALOG}.{UC_SCHEMA}` created")
        except PermissionDenied as e:
            print(
                f"FAIL: `{UC_CATALOG}.{UC_SCHEMA}` does not exist, and no permissions to create.  Please provide an existing UC Schema.")
            raise ValueError("Unity Catalog Schema `{UC_CATALOG}.{UC_SCHEMA}` does not exist.")