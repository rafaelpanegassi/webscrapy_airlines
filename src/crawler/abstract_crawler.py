from abc import ABC, abstractmethod

from src.tools.redis import RedisClient


class AbstractCrawler(ABC):
    """
    Abstract base class for web crawlers.
    """
    def __init__(self):
        self.redis = RedisClient.get()

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
        return self.redis.get(key)
