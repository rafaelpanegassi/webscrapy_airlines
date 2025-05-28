import os

import pandas as pd
from loguru import logger
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure


class MongoConnector:
    """
    A singleton MongoDB connector to manage connections and data operations.
    It loads configuration from environment variables.
    """

    _instance = None
    _client = None
    _db = None
    _collection_obj = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27017,
        database_name: str = "crawler_airlines",
        collection_name: str = "airlines_data",
    ):
        if MongoConnector._client is None:
            self.host = os.getenv("MONGO_HOST", host)
            self.port = int(os.getenv("MONGO_PORT", port))
            self.database_name_prop = os.getenv("MONGO_DATABASE", database_name)
            self.collection_name_prop = os.getenv("MONGO_COLLECTION", collection_name)
            try:
                self._connect()
            except ConnectionFailure as e:
                logger.error(f"MongoConnector initialization failed: {e}")
                raise

    def _connect(self):
        """Establishes and verifies a connection to the MongoDB server."""
        logger.info(f"Attempting to connect to MongoDB at {self.host}:{self.port}")
        try:
            MongoConnector._client = MongoClient(
                self.host, self.port, serverSelectionTimeoutMS=5000
            )
            MongoConnector._client.admin.command("ping")
            MongoConnector._db = MongoConnector._client[self.database_name_prop]
            MongoConnector._collection_obj = MongoConnector._db[
                self.collection_name_prop
            ]
            logger.info(
                f"Successfully connected to MongoDB. DB: '{self.database_name_prop}', Collection: '{self.collection_name_prop}'"
            )
        except ConnectionFailure as e:
            logger.error(
                f"Failed to connect to MongoDB at {self.host}:{self.port}: {e}"
            )
            MongoConnector._client = None
            raise

    def get_collection(self):
        """Returns the MongoDB collection object, ensuring connection."""
        if MongoConnector._collection_obj is None:
            logger.error(
                "MongoDB collection is not available. Connection might have failed or been closed."
            )
            if MongoConnector._client is None:
                logger.info("Attempting to re-initialize MongoDB connection.")
                try:
                    self._connect()
                except ConnectionFailure as e:
                    raise ConnectionError(
                        f"Failed to re-establish MongoDB connection: {e}"
                    ) from e
            if MongoConnector._collection_obj is None:
                raise ConnectionError(
                    "MongoDB collection is not initialized even after attempting reconnection."
                )
        return MongoConnector._collection_obj

    def save_dataframe(self, df_to_save: pd.DataFrame) -> bool:
        """Saves a pandas DataFrame to the configured MongoDB collection."""
        if not isinstance(df_to_save, pd.DataFrame):
            logger.error("Data to save is not a pandas DataFrame.")
            return False
        if df_to_save.empty:
            logger.info("DataFrame is empty. Nothing to save to MongoDB.")
            return True

        try:
            collection = self.get_collection()
            data_records = df_to_save.to_dict(orient="records")
            collection.insert_many(data_records)
            logger.info(
                f"Successfully saved {len(data_records)} records to MongoDB collection '{self.collection_name_prop}'."
            )
            return True
        except (OperationFailure, ConnectionFailure) as e:
            logger.error(
                f"Could not save DataFrame to MongoDB collection '{self.collection_name_prop}': {e}"
            )
        except ConnectionError as e:
            logger.error(
                f"Could not save DataFrame due to MongoDB connection issue: {e}"
            )
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while saving DataFrame to MongoDB: {e}",
                exc_info=True,
            )
        return False

    def close_connection(self):
        """Closes the MongoDB client connection."""
        if MongoConnector._client:
            MongoConnector._client.close()
            MongoConnector._client = None
            MongoConnector._db = None
            MongoConnector._collection_obj = None
            logger.info("MongoDB Connection Closed!")
