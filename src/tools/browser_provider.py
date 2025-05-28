import os

from loguru import logger
from selenium import webdriver


class BrowserProvider:
    """
    Provides configured instances of the Chrome WebDriver.
    Assumes ChromeDriver is in system PATH or its path is configured via Selenium Service.
    """

    def get_browser(
        self, custom_args: list[str] = None, run_headless: bool = True
    ) -> webdriver.Chrome:
        """
        Configures and returns a new Chrome WebDriver instance.
        """
        options = webdriver.ChromeOptions()
        effective_args = (
            custom_args if custom_args is not None else self._default_args()
        )

        self._apply_arguments(options, effective_args)
        self._configure_headless_mode(options, run_headless)

        chrome_binary_path = os.getenv("CHROME_BINARY_PATH")
        if chrome_binary_path:
            logger.info(
                f"Using Chrome browser binary path from environment variable: {chrome_binary_path}"
            )
            options.binary_location = chrome_binary_path

        try:
            logger.info(
                "Initializing Chrome WebDriver. Assumes ChromeDriver is in system PATH."
            )
            browser = webdriver.Chrome(options=options)

            logger.info("Chrome WebDriver initialized successfully.")
            return browser
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}", exc_info=True)
            logger.error(
                "Ensure Google Chrome browser IS INSTALLED and accessible. "
                "Also, ensure the ChromeDriver executable is in your system's PATH "
                "and is compatible with your Chrome browser version. "
                "If Chrome browser is in a non-standard location, set the CHROME_BINARY_PATH environment variable "
                "or modify options.binary_location in BrowserProvider."
            )
            raise

    def _apply_arguments(
        self, options_obj: webdriver.ChromeOptions, arg_list: list[str]
    ):
        """Applies a list of arguments to the ChromeOptions object."""
        if arg_list:
            for arg in arg_list:
                options_obj.add_argument(arg)

    def _configure_headless_mode(
        self, options_obj: webdriver.ChromeOptions, run_headless_param: bool
    ):
        """Configures headless mode based on environment variable and parameter."""
        env_headless = os.getenv("HEADLESS", "").strip().lower()

        if not options_obj.binary_location and (
            env_headless == "true" or run_headless_param
        ):
            logger.debug(
                "Running headless; ensure Chrome browser binary is findable or options.binary_location is set if not in PATH."
            )

        if env_headless == "true":
            logger.info(
                "Running in headless mode (forced by HEADLESS=true environment variable)."
            )
            options_obj.add_argument("--headless=new")
            options_obj.add_argument("--disable-gpu")
        elif env_headless == "false":
            logger.info(
                "Running in non-headless (headed) mode (forced by HEADLESS=false environment variable)."
            )
        elif run_headless_param:
            logger.info(
                "Running in headless mode (due to run_headless_param=True and no overriding HEADLESS env var)."
            )
            options_obj.add_argument("--headless=new")
            options_obj.add_argument("--disable-gpu")
        else:
            logger.info("Running in non-headless (headed) mode.")

    def _default_args(self) -> list[str]:
        """Returns a list of default arguments for Chrome WebDriver."""
        return [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-web-security",
            "--disable-dev-shm-usage",
            "--memory-pressure-off",
            "--ignore-certificate-errors",
            "--incognito",
            "--disable-blink-features=AutomationControlled",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "--disable-infobars",
            "--window-size=1920,1080",
            "--log-level=0",
        ]
