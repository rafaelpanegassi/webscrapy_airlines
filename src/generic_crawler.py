import json
import re

import pandas as pd
from loguru import logger
from lxml import html

from crawler.abstract_crawler import AbstractCrawler
from tools.steps.actions import action_dictionary


class GenericCrawler(AbstractCrawler):
    """
    A generic web crawler that operates based on dynamic configurations (steps and
    extraction rules) loaded from a data source like Redis.
    """

    def __init__(self, crawler_config_key: str):
        super().__init__()
        self.crawler_config_key = crawler_config_key
        self.extracted_dataframe: pd.DataFrame | None = None

        if not self._load_crawler_configuration(self.crawler_config_key):
            raise ValueError(
                f"Failed to load or parse configuration for crawler key '{self.crawler_config_key}'. Crawler cannot operate."
            )

    def start_crawling(
        self,
        origin_code: str,
        destination_code: str,
        departure_dt_str: str,
        return_dt_str: str | None = None,
    ) -> bool:
        """
        Starts the web crawling process with the given flight parameters.
        """
        self.runtime_input_data = {
            "origin": origin_code.upper(),
            "destination": destination_code.upper(),
            "departure_date": departure_dt_str,
            "return_date": return_dt_str if return_dt_str else "",
        }
        logger.info(
            f"Starting crawler '{self.crawler_config_key}' with input: {self.runtime_input_data}"
        )

        try:
            self._ensure_browser_instance()
            if not self.active_browser:
                logger.error(
                    "Browser instance is not available. Aborting crawling process."
                )
                return False

            if not self.execute_script_phases():
                logger.error("Core script phase execution failed for the crawler.")
                return False

            self.extracted_dataframe = self.extract_data_from_page()

            if (
                self.extracted_dataframe is not None
                and not self.extracted_dataframe.empty
            ):
                logger.info(
                    f"Data extraction successful. DataFrame shape: {self.extracted_dataframe.shape}"
                )
                if not self.save_extracted_data(self.extracted_dataframe):
                    logger.warning(
                        "Attempt to save extracted data to the database reported issues."
                    )
            elif self.extracted_dataframe is None:
                logger.warning(
                    "Data extraction process resulted in None (possibly due to errors or no matching data)."
                )
            else:
                logger.info(
                    "Data extraction process completed, but no data was found or the resulting DataFrame is empty."
                )

            logger.info(
                f"Crawler '{self.crawler_config_key}' has finished its execution cycle."
            )
            return True

        except RuntimeError as rte:
            logger.error(
                f"A runtime error occurred in crawler '{self.crawler_config_key}': {rte}",
                exc_info=True,
            )
            return False
        except Exception as e:
            logger.error(
                f"An unexpected critical error occurred in crawler '{self.crawler_config_key}': {e}",
                exc_info=True,
            )
            return False
        finally:
            self.close_all_resources()

    def _prepare_step_attributes(self, raw_attributes):
        """Recursively prepares step attributes by replacing placeholders like {{key}}."""

        def placeholder_replacer(match_obj: re.Match) -> str:
            key_name = match_obj.group(1).strip()
            value = self.runtime_input_data.get(key_name)
            if value is None:
                logger.warning(
                    f"Placeholder '{{{key_name}}}' not found in runtime input data. Replacing with empty string."
                )
                return ""
            return str(value)

        placeholder_pattern = r"\{\{(.*?)\}\}"

        if isinstance(raw_attributes, str):
            return re.sub(placeholder_pattern, placeholder_replacer, raw_attributes)
        elif isinstance(raw_attributes, dict):
            return {
                k: self._prepare_step_attributes(v) for k, v in raw_attributes.items()
            }
        elif isinstance(raw_attributes, list):
            return [self._prepare_step_attributes(item) for item in raw_attributes]
        else:
            return raw_attributes

    def execute_dynamic_steps(self, steps_dictionary: dict) -> bool:
        """Executes a sequence of steps (actions) defined in the steps_dictionary."""
        if not steps_dictionary:
            logger.info("No steps provided for this execution phase.")
            return True
        try:
            sorted_step_names = sorted(
                steps_dictionary.keys(),
                key=lambda x: (
                    (
                        int(x.split("-")[1])
                        if x.startswith("step-")
                        and "-" in x
                        and x.split("-")[1].isdigit()
                        else float("inf")
                    ),
                    x,
                ),
            )
        except:
            sorted_step_names = list(steps_dictionary.keys())

        for step_name in sorted_step_names:
            step_definition = steps_dictionary[step_name]
            action_name = step_definition.get("action")
            raw_attrs = step_definition.get("att")

            if not action_name or action_name not in action_dictionary:
                logger.error(
                    f"Step '{step_name}': Action '{action_name}' is invalid or not found in action_dictionary. Halting phase."
                )
                return False

            processed_attrs = self._prepare_step_attributes(raw_attrs)
            logger.info(
                f"Executing Step '{step_name}': Action='{action_name}', Processed Attributes='{processed_attrs}'"
            )
            action_function_to_call = action_dictionary[action_name]

            try:
                if not self.active_browser and action_name not in ["wait"]:
                    logger.error(
                        f"Browser not available for action '{action_name}' in step '{step_name}'. Halting phase."
                    )
                    return False

                action_succeeded = action_function_to_call(
                    self.active_browser, processed_attrs
                )

                if not action_succeeded:
                    logger.error(
                        f"Step '{step_name}' (Action: {action_name}) failed. Halting phase."
                    )
                    return False
            except Exception as e:
                logger.error(
                    f"Exception during execution of Step '{step_name}' (Action: {action_name}): {e}",
                    exc_info=True,
                )
                return False
        logger.info("Successfully completed all steps in this phase.")
        return True

    def extract_data_from_page(self) -> pd.DataFrame | None:
        """Extracts structured data from the current page content using lxml and XPath."""
        if not self.active_browser:
            logger.error("Browser is not available for data extraction.")
            return None

        logger.info("Initiating data extraction from page content.")
        extraction_rules = (
            self.crawler_steps_config.get("tag") if self.crawler_steps_config else None
        )
        if not extraction_rules:
            logger.warning(
                "No 'tag' (extraction rules) found in crawler configuration."
            )
            return pd.DataFrame()

        try:
            current_page_source = self.active_browser.page_source
            html_tree = html.fromstring(current_page_source)
        except Exception as e:
            logger.error(
                f"Failed to get page source or parse HTML for extraction: {e}",
                exc_info=True,
            )
            return None

        extracted_records = []
        group_extraction_rules = extraction_rules.get("result_group")
        if group_extraction_rules:
            container_xpath = group_extraction_rules.get("tag")
            item_definitions = group_extraction_rules.get("items")

            if not container_xpath or not item_definitions:
                logger.error(
                    "Invalid 'result_group' configuration: 'tag' or 'items' missing."
                )
            else:
                logger.info(
                    f"Extracting item groups using container XPath: {container_xpath}"
                )
                item_nodes = html_tree.xpath(container_xpath)
                logger.info(
                    f"Found {len(item_nodes)} individual item(s) to process for fields using XPath: {container_xpath}"
                )

                item_xpath_relative_to_item = item_definitions.get("tag", ".")
                field_extraction_map = item_definitions.get("elements")

                if not field_extraction_map:
                    logger.error(
                        "Invalid 'items' configuration: 'elements' map missing."
                    )
                else:
                    for item_idx, item_node_from_list in enumerate(item_nodes):
                        actual_item_nodes_to_process = item_node_from_list.xpath(
                            item_xpath_relative_to_item
                        )

                        for sub_item_idx, item_node in enumerate(
                            actual_item_nodes_to_process
                        ):
                            record = {}
                            current_item_log_prefix = f"Item list index #{item_idx + 1}, sub-item #{sub_item_idx +1}"
                            logger.debug(f"Processing {current_item_log_prefix}")

                            for field_name, field_def in field_extraction_map.items():
                                field_xpath = field_def.get("tag")
                                if not field_xpath:
                                    logger.warning(
                                        f"{current_item_log_prefix}: No XPath 'tag' for field '{field_name}'."
                                    )
                                    record[field_name] = None
                                    continue
                                try:
                                    values = item_node.xpath(field_xpath)
                                    if not values:
                                        record[field_name] = None
                                    elif len(values) == 1:
                                        val = values[0]
                                        record[field_name] = (
                                            val.text_content().strip()
                                            if hasattr(val, "text_content")
                                            else str(val).strip()
                                        )
                                    else:
                                        record[field_name] = [
                                            (
                                                v.text_content().strip()
                                                if hasattr(v, "text_content")
                                                else str(v).strip()
                                            )
                                            for v in values
                                        ]
                                    logger.debug(
                                        f"  {current_item_log_prefix} - Field '{field_name}': Extracted '{record[field_name]}'"
                                    )
                                except Exception as ex_field:
                                    logger.error(
                                        f"{current_item_log_prefix}: Error extracting field '{field_name}' with XPath '{field_xpath}': {ex_field}",
                                        exc_info=True,
                                    )
                                    record[field_name] = "EXTRACTION_ERROR"
                            if any(
                                val is not None and val != "EXTRACTION_ERROR"
                                for val in record.values()
                            ):
                                extracted_records.append(record)
                            else:
                                logger.debug(
                                    f"{current_item_log_prefix} resulted in no valid data. Discarding."
                                )
        single_extraction_rules = extraction_rules.get("result_single")
        if single_extraction_rules:
            logger.warning("'result_single' extraction logic is not implemented.")

        if not extracted_records:
            logger.info(
                "No records were extracted based on the provided rules and page content."
            )
            return pd.DataFrame()
        logger.info(
            f"Data extraction complete. {len(extracted_records)} records found."
        )
        return pd.DataFrame(extracted_records)
