from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput
from databricks.sdk.service.vectorsearch import EndpointType, DeltaSyncVectorIndexSpecRequest, PipelineType, EmbeddingSourceColumn, VectorIndexType

import logging
from utils.uc_model_version import get_latest_model_version


class VectorSearchInfra():
    def __init__(self, config):
        self.w = WorkspaceClient()

        self.config = config

        # get defaults from config file
        self.default_VS_endpoint_name = self.config.get("VECTOR_SEARCH_ENDPOINT_NAME")
        self.default_embedding_endpoint_name = self.config.get("EMBEDDING_MODEL_ENDPOINT_NAME")
        self.default_embedding_model_UC_path = self.config.get("EMBEDDING_MODEL_UC_PATH")

        # these are updated as the user makes a choice about which VS endpoint and embedding model to use.
        # the chosen values are then written back into the config file.
        self.migration_assistant_VS_endpoint = None
        self.migration_assistant_embedding_model_name = None

        # these are not configurable by the end user
        self.migration_assistant_VS_index = f"{self.config.get('CATALOG')}.{self.config.get('SCHEMA')}.{self.config.get('VS_INDEX_NAME')}"
        self.migration_assistant_VS_table = f"{self.config.get('CATALOG')}.{self.config.get('SCHEMA')}.{self.config.get('CODE_INTENT_TABLE_NAME')}"


    def choose_VS_endpoint(self):
        '''Ask the user to choose an existing vector search endpoint or create a new one.
        '''
        endpoints = [f"CREATE NEW VECTOR SEARCH ENDPOINT: {self.default_VS_endpoint_name}"]
        # Create a list of all endpoints in the workspace. Returns a generator
        endpoints.extend(list(self.w.vector_search_endpoints.list_endpoints()))

        print("Choose a Vector Search endpoint:")
        for i, endpoint in enumerate(endpoints):
            try:
                print(f"{i}: {endpoint.name} ({endpoint.num_indexes} indexes)")
            except:
                print(f"{i}: {endpoint}")
        choice = int(input())
        if choice == 0:
            self.migration_assistant_VS_endpoint = self.default_VS_endpoint_name
            logging.info(f"Creating new VS endpoint {self.migration_assistant_VS_endpoint}."
                         f"This will take a few minutes."
                         f"Check status here: {self.w.config.host}/compute/vector-search/{self.migration_assistant_VS_endpoint}")
            self.create_VS_endpoint()
        else:
            self.migration_assistant_VS_endpoint = endpoints[choice].name
            # update config with user choice
            self.config['VECTOR_SEARCH_ENDPOINT_NAME'] = self.migration_assistant_VS_endpoint

    def choose_embedding_model(self):
        # list all serving endpoints with a task of embedding
        endpoints = [f"CREATE NEW EMBEDDING MODEL ENDPOINT {self.default_embedding_endpoint_name} USING"
                     f" {self.default_embedding_model_UC_path}"]

        endpoints.extend(list(filter(lambda x: "embedding" in x.task if x.task else False,  self.w.serving_endpoints.list())))
        print("Choose an embedding model endpoint:")
        for i, endpoint in enumerate(endpoints):
            try:
                print(f"{i}: {endpoint.name}")
            except:
                print(f"{i}: {endpoint}")
        choice = int(input())
        if choice == 0:
            self.migration_assistant_embedding_model_name = self.default_embedding_endpoint_name
            logging.info(f"Creating new model serving endpoint {self.migration_assistant_embedding_model_name}. "
                         f"This will take a few minutes."
                         f"Check status here: {self.w.config.host}/ml/endpoints/{self.migration_assistant_embedding_model_name}")
            self.create_embedding_model_endpoint()
        else:
            self.migration_assistant_embedding_model_name = endpoints[choice].name
            self.config['EMBEDDING_MODEL_ENDPOINT_NAME'] = self.migration_assistant_embedding_model_name

    def create_embedding_model_endpoint(self):


        latest_version = get_latest_model_version(model_name=self.default_embedding_model_UC_path)
        latest_version = str(latest_version)

        self.w.serving_endpoints.create(
            name=self.migration_assistant_embedding_model_name
            ,config=EndpointCoreConfigInput(
                name=self.migration_assistant_embedding_model_name
                ,served_entities=[
                    ServedEntityInput(
                        entity_name=self.default_embedding_model_UC_path
                        ,entity_version=latest_version
                        ,name=self.migration_assistant_embedding_model_name
                        ,scale_to_zero_enabled=True
                        ,workload_type="GPU_SMALL"
                        ,workload_size="Small"
                    )
                ]
            )
        )

    def create_VS_endpoint(self):
        self.w.vector_search_endpoints.create_endpoint(
            name = self.migration_assistant_VS_endpoint,
            endpoint_type = EndpointType.STANDARD
        )

    def create_VS_index(self):
        self.w.vector_search_indexes.create_index(
            name=self.migration_assistant_VS_index
            ,endpoint_name=self.migration_assistant_VS_endpoint
            ,primary_key="id"
            ,index_type=VectorIndexType.DELTA_SYNC
            ,delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
                source_table=self.migration_assistant_VS_table
                ,pipeline_type=PipelineType.TRIGGERED
                ,embedding_source_columns=[
                    EmbeddingSourceColumn(
                        embedding_model_endpoint_name=self.migration_assistant_embedding_model_name
                        ,name="intent"
                    )
                ]
            )

        )


