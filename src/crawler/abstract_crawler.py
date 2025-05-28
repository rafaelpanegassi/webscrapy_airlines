from abc import ABC, abstractmethod

import pandas as pd
from loguru import logger
from selenium.webdriver.remote.webdriver import WebDriver

from tools.browser_provider import BrowserProvider
from tools.mongo_connector import MongoConnector
from tools.redis_client import RedisClient


class AbstractCrawler(ABC):
    """
    Abstract base class for web crawlers.
    Initializes common dependencies like database connectors and browser provider.
    Defines the core workflow and abstract methods for specific crawler implementations.
    """

    def __init__(self):
        try:
            self.redis_client = RedisClient()
            self.mongo_connector = MongoConnector()
            self.browser_provider = BrowserProvider()
            self.active_browser: WebDriver | None = None
        except (ConnectionError, RuntimeError, Exception) as e:
            logger.critical(
                f"Failed to initialize core components for AbstractCrawler: {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Core component initialization failed, crawler cannot operate: {e}"
            ) from e

        self.crawler_steps_config: dict | None = None
        self.runtime_input_data: dict = {}

    def _ensure_browser_instance(self) -> WebDriver:
        """Ensures an active browser instance is available, creating one if necessary."""
        if self.active_browser is None:
            logger.info("Requesting new browser instance from provider.")
            self.active_browser = self.browser_provider.get_browser()
        if self.active_browser is None:
            raise RuntimeError("Failed to obtain a valid browser instance.")
        return self.active_browser

    def _load_crawler_configuration(self, config_key: str) -> bool:
        """Loads crawler steps and extraction rules from Redis using the config_key."""
        logger.info(f"Loading crawler configuration from Redis for key: {config_key}")
        config_json_str = self.redis_client.get_data(config_key)
        if config_json_str is None:
            logger.error(f"No configuration found in Redis for key: {config_key}.")
            return False
        try:
            self.crawler_steps_config = pd.read_json(
                config_json_str, typ="series"
            ).to_dict()
            logger.info(
                f"Successfully loaded and parsed configuration for '{config_key}'."
            )
            return True
        except ValueError as e:
            logger.error(
                f"Error parsing JSON configuration for key '{config_key}': {e}"
            )
            self.crawler_steps_config = None
            return False

    def execute_script_phases(self) -> bool:
        """Executes the 'before', 'main', and 'after' phases of the crawler script."""
        if not self.crawler_steps_config or "script" not in self.crawler_steps_config:
            logger.error("Crawler configuration or 'script' section is missing.")
            return False

        script_phases = self.crawler_steps_config.get("script", {})

        logger.info("Executing 'before' script phase...")
        if not self.execute_dynamic_steps(script_phases.get("before", {})):
            logger.warning("'before' script phase execution reported issues or failed.")

        logger.info("Executing 'main' script phase...")
        main_phase_steps = script_phases.get("main")
        if not main_phase_steps:
            logger.error(
                "'main' script phase is undefined. Cannot proceed with core logic."
            )
            return False
        if not self.execute_dynamic_steps(main_phase_steps):
            logger.error(
                "'main' script phase execution failed. Halting crawler operations."
            )
            return False

        logger.info("Executing 'after' script phase...")
        if not self.execute_dynamic_steps(script_phases.get("after", {})):
            logger.warning("'after' script phase execution reported issues or failed.")

        return True

    @abstractmethod
    def execute_dynamic_steps(self, steps_dictionary: dict) -> bool:
        """
        Dynamically executes a sequence of steps defined in a dictionary.
        """
        pass

    @abstractmethod
    def _prepare_step_attributes(self, raw_attributes):
        """
        Prepares attributes for a step, typically by substituting placeholder values.
        """
        pass

    @abstractmethod
    def extract_data_from_page(self) -> pd.DataFrame | None:
        """
        Extracts data from the current web page based on rules in the configuration.
        """
        pass

    def save_extracted_data(self, data_df: pd.DataFrame) -> bool:
        """Saves the provided DataFrame to MongoDB."""
        if not isinstance(data_df, pd.DataFrame):
            logger.warning(
                "Invalid data type passed to save_extracted_data; expected DataFrame."
            )
            return False
        if data_df.empty:
            logger.info("DataFrame is empty, no data to save to MongoDB.")
            return True

        logger.info(
            f"Attempting to save DataFrame (shape: {data_df.shape}) to MongoDB."
        )
        try:
            was_saved = self.mongo_connector.save_dataframe(data_df)
            if was_saved:
                logger.info("Data successfully saved to MongoDB.")
            else:
                logger.error(
                    "Failed to save data to MongoDB (connector returned False)."
                )
            return was_saved
        except Exception as e:
            logger.error(
                f"Unexpected error during save_extracted_data: {e}", exc_info=True
            )
            return False

    def close_all_resources(self):
        """Closes the web browser and any other managed resources."""
        if self.active_browser:
            logger.info("Closing browser instance.")
            try:
                self.active_browser.quit()
                self.active_browser = None
            except Exception as e:
                logger.error(f"Error encountered while quitting browser: {e}")
