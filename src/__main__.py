from generic_crawler import GenericCrawler
from loguru import logger

latam = GenericCrawler("Latam").start("GRU", "CGB", "2025-10-12", "2025-11-12")
# latam = GenericCrawler("Latam").start()
# azul = GenericCrawler("Azul").start()


logger.info("Crawler executed!")
