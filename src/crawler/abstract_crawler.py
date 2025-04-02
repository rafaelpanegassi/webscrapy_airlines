from abc import ABC, abstractmethod

from loguru import logger

from tools.browser_provider import BrowserProvider
from tools.mongodb import MongoConnection
from tools.redis import RedisClient


class AbstractCrawler(ABC):

    def __init__(self):
        self.redis = RedisClient.get()
        self.mongo = MongoConnection()
        self.browser = BrowserProvider().get_browser()

    def execute_steps(self):
        steps = self.steps["script"]
        if steps["before"]:
            self.dynamic_steps(steps["before"])
        if steps["main"]:
            self.dynamic_steps(steps["main"])
        if steps["after"]:
            self.dynamic_steps(steps["after"])

    @abstractmethod
    def dynamic_steps(self, steps):
        pass

    def get_step(self, key):
        steps = None
        try:
            steps = self.redis.get(key)
        except Exception as e:
            logger.error(f'Impossible to catch data from Redis: {e}')
        return steps

    def save_data(self, data):
        try:
            self.mongo.save_dataframe(data)
        except Exception as e:
            logger.error(f'Error to save in MongoDB: {e}')
