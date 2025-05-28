import os

import redis
from loguru import logger


class RedisClient:
    """
    A singleton Redis client to manage connections to a Redis server.
    It loads configuration from environment variables and provides a method to get data.
    """

    _instance = None
    _redis_client_instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisClient, cls).__new__(cls, *args, **kwargs)
            try:
                cls._instance._redis_client_instance = cls._instance._connect_to_redis()
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Could not initialize RedisClient: {e}")
                raise
        return cls._instance

    @staticmethod
    def _load_config() -> dict:
        """Loads Redis connection configuration from environment variables."""
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "decode_responses": True,
        }

    @classmethod
    def _connect_to_redis(cls) -> redis.StrictRedis:
        """Establishes and verifies a connection to the Redis server."""
        config = cls._load_config()
        logger.info(
            f"Attempting to connect to Redis at {config['host']}:{config['port']}"
        )
        try:
            client = redis.StrictRedis(**config)
            client.ping()
            logger.info("Successfully connected to Redis.")
            return client
        except redis.exceptions.ConnectionError as e:
            logger.error(
                f"Failed to connect to Redis at {config['host']}:{config['port']}: {e}"
            )
            raise

    @classmethod
    def get_client(cls) -> redis.StrictRedis:
        """
        Returns the active Redis client instance.
        Ensures the instance is created and the client is connected.
        """
        if cls._instance is None or cls._instance._redis_client_instance is None:
            logger.info(
                "Redis client not initialized or connection failed previously. Attempting to (re)initialize."
            )
            instance = cls()
            if instance._redis_client_instance is None:
                raise ConnectionError(
                    "Failed to get a valid Redis client connection after re-initialization attempt."
                )
            return instance._redis_client_instance
        return cls._instance._redis_client_instance

    def get_data(self, key: str) -> str | None:
        """Fetches data from Redis for the given key."""
        try:
            client = self.get_client()
            value = client.get(key)
            if value is None:
                logger.warning(f"No data found in Redis for key: {key}")
            return value
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error when getting key '{key}': {e}")
            return None
        except ConnectionError as e:
            logger.error(
                f"Could not get data for key '{key}' due to Redis connection issue: {e}"
            )
            return None
