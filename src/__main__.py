from generic_crawler import GenericCrawler
from loguru import logger

def main():
    try:
        # Configure logger to show more information
        logger.add("crawler_debug.log", level="DEBUG", rotation="10 MB")
        
        # Start the crawler
        logger.info("Starting Latam crawler")
        latam = GenericCrawler("Latam")
        latam.start("GRU", "CGB", "2025-10-12", "2025-11-12")

        
        logger.info("Crawler executed successfully!")
    except Exception as e:
        logger.error(f"Error running crawler: {e}")

if __name__ == "__main__":
    main()