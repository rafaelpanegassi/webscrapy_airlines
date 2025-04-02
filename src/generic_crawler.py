import json
import re

from bs4 import BeautifulSoup
from loguru import logger
from lxml import html

from crawler.abstract_crawler import AbstractCrawler
from tools.steps.actions import action_dict


class GenericCrawler(AbstractCrawler):

    def __init__(self, type):
        super().__init__()
        self.type = type
        self.steps = json.loads(self.get_step(self.type))
        self.data_frame = None
        if self.steps is None:
            logger.error('You need to configure crawler')

    def start(self, origin, destiny, departure_time, return_date):
        self.input = {
            "origin": origin,
            "destiny": destiny,
            "departure_time": departure_time,
            "return_date": return_date
        }
        self.execute_steps()
        self.extraction()
        self.save_data(self.data_frame)
        self.browser.close()
        return

    def dynamic_steps(self, steps):
        if steps:
            for step in steps:
                s = steps[step]
                action = s["action"]
                att = self.preparing_steps(s["att"])
                if action_dict[action] is None:
                    logger.error("Step not created")
                    action_dict[action](self.browser, att)
        return

    def preparing_steps(self, att):

        def custom_replace(match):
            key = match.group(1)
            return self.input.get(key, '')

        if isinstance(att, dict):
            pattern = r"\{\{(.*?)\}\}"
            pattern2 = r'\{\{([^}]+)\}\}'
            match = re.search(pattern, att["value"])
            match1 = re.search(pattern, att["element"])
            if match:
                att["value"] = self.input[match.group(1)]
            if match1:
                att["element"] = re.sub(pattern2, custom_replace, att["element"])
        else:
            pattern = r"\{\{(.*?)\}\}"
            match = re.findall(pattern, str(att))
            if match:
                att = re.sub(pattern, custom_replace, att)
        return att

    def extraction(self):
        self.html = self.browser.page_source
        soup = BeautifulSoup(self.html, "html.parser")
        tree = html.fromstring(self.html)
        tags = self.steps["tag"]
        content = []
        if tags:
            if tags["result_group"] is None and tags["result_single"] is None:
                logger.error("Tags for extraction not created!")
            if tags.get("result_single"):
                pass
            if tags.get("result_group"):
                tag = tags["result_group"]["tag"]
                items = tags["result_group"]["items"]
                results = tree.xpath(tag)
                for result in results:
                    subresult = result.xpath(items["tag"])
                    elements = items["elements"]
                    for sr in subresult:
                        arr = dict()
                        for element in elements:
                            t = elements[element]["tag"]
                            r = sr.xpath(t)
                            x = []
                            for el in r:
                                x.append(el.text_content())
                            arr[element] = x
                        content.append(arr)
                    logger.info(content)
        return
