from abc import ABC, abstractmethod

from loguru import logger

from src.tools.mongodb import MongoConnection
from src.tools.redis import RedisClient
from src.tools.browser_provider import BrowserProvider


class AbstractCrawler(ABC):
    """
    Abstract base class for web crawlers.
    """
    def __init__(self):
        self.redis = RedisClient.get()
        self.mongo = MongoConnection()
        self.browser = BrowserProvider()

    @abstractmethod
    def execute_main(self):
        """
        Execute the main crawling process.
        """
        pass

    @abstractmethod
    def execute_before(self):
        """
        Execute any pre-crawling setup.
        """
        pass

    @abstractmethod
    def execute_after(self):
        """
        Execute any post-crawling cleanup.
        """
        pass

    def get_step(self, key):
        """
        Get the current step of the crawler.
        """
        steps = None
        try:
            steps = self.redis.get(key)
        except Exception as e:
            logger.error(f'Error collecting data from Redis: {e}')
            return steps

    def save_data(self, data):
        try:
            self.mongo.save_dataframe(data)
        except Exception as e:
            logger.error(f'Error saving to MongoDB: {e}')
