import json
import re

import pandas as pd
from loguru import logger
from lxml import html

from crawler.abstract_crawler import AbstractCrawler
from tools.steps.actions import action_dict


class GenericCrawler(AbstractCrawler):
    def __init__(self, type):
        super().__init__()
        self.type = type
        step_data = self.get_step(self.type)
        if step_data is None:
            logger.error('You need to configure crawler')
            return
        self.steps = json.loads(step_data)
        self.data_frame = None

    def start(self, origin, destiny, departure_date, return_date):
        self.input = {
            "origin": origin,
            "destiny": destiny,
            "departure_date": departure_date,
            "return_date": return_date
        }
        logger.info(f"Starting crawler with input: {self.input}")
        self.execute_steps()
        self.extraction()
        if self.data_frame is not None:
            self.save_data(self.data_frame)
        self.browser.close()
        return

    def dynamic_steps(self, steps):
        if steps:
            for step in steps:
                s = steps[step]
                action = s["action"]
                att = self.preparing_steps(s["att"])
                logger.info(f"Executing step: {step}, action: {action}, attributes: {att}")
                if action not in action_dict:
                    logger.error(f"Action {action} not found in action_dict")
                    continue
                try:
                    action_dict[action](self.browser, att)
                except Exception as e:
                    logger.error(f"Error executing action {action}: {e}")
        return

    def preparing_steps(self, att):
        def custom_replace(match):
            key = match.group(1)
            return self.input.get(key, '')
        pattern = r"\{\{(.*?)\}\}"
        pattern2 = r'\{\{([^}]+)\}\}'
        if isinstance(att, dict):
            match = re.search(pattern, att.get("value", ""))
            match1 = re.search(pattern, att.get("element", ""))

            if match and "value" in att:
                att["value"] = self.input.get(match.group(1), "")
            if match1 and "element" in att:
                att["element"] = re.sub(pattern2, custom_replace, att["element"])
        else:
            match = re.findall(pattern, str(att))
            if match:
                att = re.sub(pattern, custom_replace, att)
        logger.debug(f"Prepared attributes: {att}")
        return att

    def extraction(self):
        try:
            self.html = self.browser.page_source
            tree = html.fromstring(self.html)
            if "tag" not in self.steps:
                logger.error("No tag configuration found in steps")
                return
            tags = self.steps["tag"]
            content = []
            if tags:
                if not tags.get("result_group") and not tags.get("result_single"):
                    logger.error("Tags for extraction not created!")
                    return
                if tags.get("result_single"):
                    logger.warning("result_single extraction not implemented")
                    pass
                if tags.get("result_group"):
                    tag = tags["result_group"]["tag"]
                    items = tags["result_group"]["items"]
                    logger.info(f"Extracting with XPath: {tag}")
                    results = tree.xpath(tag)
                    logger.info(f"Found {len(results)} results")
                    for result in results:
                        subresult = result.xpath(items["tag"])
                        elements = items["elements"]
                        for sr in subresult:
                            arr = dict()
                            for element in elements:
                                t = elements[element]["tag"]
                                r = sr.xpath(t)
                                if len(r) == 1:
                                    try:
                                        arr[element] = r[0].text_content().strip()
                                    except Exception as e:
                                        logger.error(f"Error extracting single text content: {e}")
                                        arr[element] = ""
                                else:
                                    x = []
                                    for el in r:
                                        try:
                                            x.append(el.text_content().strip())
                                        except Exception as e:
                                            logger.error(f"Error extracting text content: {e}")
                                    arr[element] = x
                            if any(arr.values()):
                                content.append(arr)
                    logger.info(f"Extracted {len(content)} items")
                    if content:
                        self.data_frame = pd.DataFrame(content)
                        logger.info(f"Created DataFrame with shape: {self.data_frame.shape}")
                    else:
                        logger.warning("No content extracted, DataFrame not created")
                        self.data_frame = None
            else:
                logger.error("No tags configuration provided")
        except Exception as e:
            logger.error(f"Error in extraction: {e}")
            self.data_frame = None
        return
