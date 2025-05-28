import time

from loguru import logger
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_INTERACTION_TIMEOUT = 15


def navigate_to_url(browser: WebDriver, url: str) -> bool:
    """Navigates the browser to the specified URL."""
    try:
        logger.info(f"Navigating to URL: {url}")
        browser.get(url)
        return True
    except Exception as e:
        logger.error(f"Error navigating to {url}: {e}")
        return False


def click_element(browser: WebDriver, attributes: dict) -> bool:
    """Finds and clicks an element specified by its XPath selector."""
    xpath_selector = attributes.get("element")
    if not xpath_selector:
        logger.error("No 'element' (XPath selector) provided for click_element action.")
        return False
    try:
        logger.debug(f"Attempting to click element with XPath: {xpath_selector}")
        button = WebDriverWait(browser, DEFAULT_INTERACTION_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, xpath_selector))
        )
        button.click()
        logger.info(f"Successfully clicked element: {xpath_selector}")
        return True
    except TimeoutException:
        logger.error(
            f"Timeout: Element not clickable or not found within {DEFAULT_INTERACTION_TIMEOUT}s: {xpath_selector}"
        )
    except ElementNotInteractableException:
        logger.error(
            f"ElementNotInteractableException: Element found but not interactable: {xpath_selector}"
        )
    except Exception as e:
        logger.error(f"Error clicking element {xpath_selector}: {e}", exc_info=True)
    return False


def type_into_element(browser: WebDriver, attributes: dict) -> bool:
    """Types text into an input field specified by its XPath selector."""
    xpath_selector = attributes.get("element")
    text_to_type = attributes.get("value", "")

    if not xpath_selector:
        logger.error(
            "No 'element' (XPath selector) provided for type_into_element action."
        )
        return False
    try:
        logger.debug(f"Attempting to type into element with XPath: {xpath_selector}")
        input_field = WebDriverWait(browser, DEFAULT_INTERACTION_TIMEOUT).until(
            EC.visibility_of_element_located((By.XPATH, xpath_selector))
        )
        input_field.clear()
        input_field.send_keys(text_to_type)
        logger.info(f"Successfully typed '{text_to_type}' into: {xpath_selector}")
        return True
    except TimeoutException:
        logger.error(
            f"Timeout: Input field not visible or not found within {DEFAULT_INTERACTION_TIMEOUT}s: {xpath_selector}"
        )
    except Exception as e:
        logger.error(f"Error typing into {xpath_selector}: {e}", exc_info=True)
    return False


def press_key_on_element(browser: WebDriver, attributes: dict) -> bool:
    """Presses a special key on a target element or the currently active element."""
    xpath_selector = attributes.get("element")
    key_name = attributes.get("value", "").lower()

    key_mapping = {
        "return": Keys.RETURN,
        "enter": Keys.ENTER,
        "escape": Keys.ESCAPE,
    }

    if key_name not in key_mapping:
        logger.error(
            f"Unsupported key value '{key_name}'. Supported keys: {list(key_mapping.keys())}"
        )
        return False

    selenium_key_code = key_mapping[key_name]

    try:
        target_element: WebElement | None = None
        if xpath_selector:
            logger.debug(
                f"Attempting to press '{key_name}' on element with XPath: {xpath_selector}"
            )
            target_element = WebDriverWait(browser, DEFAULT_INTERACTION_TIMEOUT).until(
                EC.visibility_of_element_located((By.XPATH, xpath_selector))
            )
        else:
            logger.debug(
                f"Attempting to press '{key_name}' on the currently active element."
            )
            target_element = browser.switch_to.active_element

        if target_element:
            target_element.send_keys(selenium_key_code)
            logger.info(f"Successfully pressed key '{key_name}' on target.")
            return True
        else:
            logger.warning("No target element found to press key on.")
            return False
    except TimeoutException:
        target_description = xpath_selector if xpath_selector else "active element"
        logger.error(
            f"Timeout: Element for key press not found/visible: {target_description}"
        )
    except Exception as e:
        logger.error(f"Error pressing key '{key_name}': {e}", exc_info=True)
    return False


def static_wait(browser: WebDriver, duration_seconds_attr) -> bool:
    """Performs a static wait. Use sparingly; prefer explicit waits."""
    try:
        duration = int(duration_seconds_attr)
        if duration <= 0:
            logger.warning(
                f"Wait duration ({duration}s) is not positive. Skipping wait."
            )
            return True
        logger.info(f"Performing static wait for {duration} seconds.")
        time.sleep(duration)
        return True
    except ValueError:
        logger.error(
            f"Invalid duration for wait action: '{duration_seconds_attr}'. Must be an integer."
        )
        return False
    except Exception as e:
        logger.error(f"Error during static_wait action: {e}", exc_info=True)
        return False


action_dictionary = {
    "goto": navigate_to_url,
    "input": type_into_element,
    "press_key": press_key_on_element,
    "click_element": click_element,
    "wait": static_wait,
}
