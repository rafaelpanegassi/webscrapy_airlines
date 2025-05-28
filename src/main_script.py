import sys
from pathlib import Path

from loguru import logger

try:
    CURRENT_SCRIPT_PATH = Path(__file__).resolve()
    SRC_DIR = CURRENT_SCRIPT_PATH.parent
    sys.path.append(str(SRC_DIR))

    from generic_crawler import GenericCrawler
except ImportError as e:
    print(
        f"CRITICAL: Failed to import GenericCrawler. Ensure it's in 'src/' and __init__.py files are present. Error: {e}"
    )
    sys.exit(1)
except Exception as e:
    print(f"CRITICAL: An error occurred during initial setup: {e}")
    sys.exit(1)


try:
    PROJECT_ROOT = SRC_DIR.parent
    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE_PATH_MAIN = LOG_DIR / "main_script_execution.log"

    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    logger.add(LOG_FILE_PATH_MAIN, rotation="5 MB", level="DEBUG", encoding="utf-8")
except Exception as e:
    logger.error(f"Could not configure file logging for main_script: {e}")


def execute_sample_crawler_run():
    """
    Example function to run a specific crawler directly.
    Useful for testing, debugging, or scheduled batch executions.
    """
    target_crawler_key = "Latam"
    origin_airport_code = "GRU"
    destination_airport_code = "MIA"
    departure_date_str = "2025-10-20"
    return_date_str = "2025-10-27"

    logger.info(
        f"--- Starting direct execution of crawler '{target_crawler_key}' via main_script.py ---"
    )
    logger.info(
        f"Parameters: Origin={origin_airport_code}, Destination={destination_airport_code}, Departure={departure_date_str}, Return={return_date_str}"
    )

    try:
        crawler = GenericCrawler(crawler_config_key=target_crawler_key)
        run_completed_successfully = crawler.start_crawling(
            origin_code=origin_airport_code,
            destination_code=destination_airport_code,
            departure_dt_str=departure_date_str,
            return_dt_str=return_date_str,
        )

        if run_completed_successfully:
            logger.info(
                f"Crawler '{target_crawler_key}' executed successfully via main_script.py."
            )
            if (
                crawler.extracted_dataframe is not None
                and not crawler.extracted_dataframe.empty
            ):
                logger.info(
                    f"Extracted data ({crawler.extracted_dataframe.shape[0]} rows)."
                )
            elif crawler.extracted_dataframe is not None:
                logger.info("The crawler ran, but no data was extracted.")
        else:
            logger.error(
                f"Crawler '{target_crawler_key}' reported a failure during its execution via main_script.py."
            )
    except ValueError as val_err:
        logger.critical(
            f"VALUE ERROR configuring crawler '{target_crawler_key}': {val_err}"
        )
    except (ConnectionError, RuntimeError) as conn_runtime_err:
        logger.critical(
            f"CONNECTION or RUNTIME ERROR during execution of '{target_crawler_key}': {conn_runtime_err}",
            exc_info=True,
        )
    except Exception as general_exc:
        logger.critical(
            f"Unexpected FATAL ERROR during execution of '{target_crawler_key}' via main_script.py: {general_exc}",
            exc_info=True,
        )
    finally:
        logger.info(
            f"--- Finished attempt to execute crawler '{target_crawler_key}' via main_script.py ---"
        )


if __name__ == "__main__":
    execute_sample_crawler_run()
    logger.info("main_script.py finished.")
