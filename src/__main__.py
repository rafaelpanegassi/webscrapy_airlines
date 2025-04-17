from loguru import logger

from generic_crawler import GenericCrawler


def main():
    try:
        #logger.add("crawler_debug.log", level="DEBUG", rotation="10 MB")
        logger.info("Starting Latam crawler")
        latam = GenericCrawler("Latam")
        latam.start("GRU", "CGB", "2025-07-12", "2025-11-12")

        logger.info("Crawler executed successfully!")
    except Exception as e:
        logger.error(f"Error running crawler: {e}")


if __name__ == "__main__":
    main()
