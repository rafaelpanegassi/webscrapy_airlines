import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from loguru import logger

try:
    CURRENT_SCRIPT_PATH = Path(__file__).resolve()
    SRC_DIR = CURRENT_SCRIPT_PATH.parent.parent
    if not (SRC_DIR / "crawler").is_dir():
        SRC_DIR = CURRENT_SCRIPT_PATH.parent
    sys.path.append(str(SRC_DIR))

    from generic_crawler import GenericCrawler
except ImportError as e:
    st.error(
        f"Failed to import GenericCrawler. Ensure it's in the correct path relative to 'src'. Error: {e}"
    )
    st.stop()
except Exception as e:
    st.error(f"An error occurred during initial setup: {e}")
    st.stop()


try:
    PROJECT_ROOT = SRC_DIR.parent
    LOG_DIR = PROJECT_ROOT / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE_PATH = LOG_DIR / "streamlit_app.log"

    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    logger.add(
        LOG_FILE_PATH,
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        encoding="utf-8",
    )
except Exception as e:
    st.warning(f"Could not configure file logging: {e}")

st.set_page_config(page_title="Flight Crawler", page_icon="✈️", layout="wide")

st.markdown(
    """
    <style>
    .main { padding: 1rem; }
    .stButton>button { width: 100%; }
    .stDateInput>div>div>input { text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- Sample IATA Data for Validation (Simplified) ---
AIRPORT_INFO_SAMPLE = {
    "GRU": "São Paulo/Guarulhos International Airport, Brazil",
    "CGH": "São Paulo/Congonhas Airport, Brazil",
    "GIG": "Rio de Janeiro/Galeão International Airport, Brazil",
    "SDU": "Rio de Janeiro/Santos Dumont Airport, Brazil",
    "BSB": "Brasília International Airport, Brazil",
    "CNF": "Belo Horizonte/Confins International Airport, Brazil",
    "SSA": "Salvador International Airport, Brazil",
    "FOR": "Fortaleza International Airport, Brazil",
    "REC": "Recife/Guararapes International Airport, Brazil",
    "POA": "Porto Alegre/Salgado Filho International Airport, Brazil",
    "CWB": "Curitiba/Afonso Pena International Airport, Brazil",
    "VCP": "Campinas/Viracopos International Airport, Brazil",
    "FLN": "Florianópolis International Airport, Brazil",
    "BEL": "Belém/Val de Cans International Airport, Brazil",
    "MAO": "Manaus/Eduardo Gomes International Airport, Brazil",
    "CGB": "Cuiabá/Marechal Rondon International Airport, Brazil",
    "JFK": "John F. Kennedy International Airport, NY, USA",
    "LAX": "Los Angeles International Airport, CA, USA",
    "LHR": "London Heathrow Airport, UK",
    "CDG": "Charles de Gaulle Airport, Paris, France",
    "FRA": "Frankfurt Airport, Germany",
    "AMS": "Amsterdam Airport Schiphol, Netherlands",
    "DXB": "Dubai International Airport, UAE",
    "HND": "Tokyo Haneda Airport, Japan",
}
RECOGNIZED_IATA_CODES = list(AIRPORT_INFO_SAMPLE.keys())


def is_valid_iata_code(code: str) -> bool:
    return code.upper() in RECOGNIZED_IATA_CODES


def run_crawler_task(
    crawler_key, origin, destination, departure_date_str, return_date_str
):
    try:
        logger.info(
            f"Attempting to start crawler '{crawler_key}' for {origin}->{destination} (Dep: {departure_date_str}, Ret: {return_date_str})"
        )
        crawler_instance = GenericCrawler(crawler_config_key=crawler_key)
        execution_successful = crawler_instance.start_crawling(
            origin, destination, departure_date_str, return_date_str
        )
        extracted_df = crawler_instance.extracted_dataframe
        if execution_successful:
            if extracted_df is not None and not extracted_df.empty:
                return (
                    True,
                    f"Crawler '{crawler_key}' executed. Results below or in database.",
                    extracted_df,
                )
            else:
                return (
                    True,
                    f"Crawler '{crawler_key}' executed. No data was extracted or saved. Check logs.",
                    pd.DataFrame(),
                )
        else:
            return (
                False,
                f"Crawler '{crawler_key}' reported an issue during execution. Check logs.",
                None,
            )
    except ValueError as ve:
        error_message = f"Configuration error starting crawler '{crawler_key}': {ve}"
        logger.error(error_message)
        return False, error_message, None
    except (ConnectionError, RuntimeError) as cre:
        error_message = (
            f"Connection or Runtime error for crawler '{crawler_key}': {cre}"
        )
        logger.error(error_message, exc_info=True)
        return False, error_message, None
    except Exception as e:
        error_message = f"Unexpected error executing crawler '{crawler_key}': {e}"
        logger.error(error_message, exc_info=True)
        return False, error_message, None


st.title("✈️ Dynamic Flight Crawler")
st.markdown("Configure and run the web scraper to fetch flight data.")

with st.sidebar:
    st.header("⚙️ Crawler Parameters")
    selected_crawler_key = st.selectbox(
        "Airline (Redis Config Key):",
        options=["Latam", "Gol", "Azul", "Avianca"],
        key="crawler_key_selector",
        help="Select the airline configuration from Redis.",
    )
    st.subheader("🛫 Route")
    col_origin, col_destination = st.columns(2)
    with col_origin:
        origin_iata_code = st.text_input(
            "Origin (IATA):", value="GRU", max_chars=3, key="origin_iata_input"
        ).upper()
        if origin_iata_code and not is_valid_iata_code(origin_iata_code):
            st.warning(
                f"'{origin_iata_code}' unrecognized. E.g., {', '.join(RECOGNIZED_IATA_CODES[:3])}..."
            )
        elif origin_iata_code:
            st.caption(AIRPORT_INFO_SAMPLE.get(origin_iata_code, "Unknown Airport"))
    with col_destination:
        destination_iata_code = st.text_input(
            "Destination (IATA):",
            value="CGB",
            max_chars=3,
            key="destination_iata_input",
        ).upper()
        if destination_iata_code and not is_valid_iata_code(destination_iata_code):
            st.warning(f"'{destination_iata_code}' unrecognized.")
        elif destination_iata_code:
            st.caption(
                AIRPORT_INFO_SAMPLE.get(destination_iata_code, "Unknown Airport")
            )

    st.subheader("🗓️ Dates")
    current_date = datetime.now().date()
    default_dept_date = current_date + timedelta(days=30)
    default_ret_date = default_dept_date + timedelta(days=7)
    departure_date = st.date_input(
        "Departure Date:",
        value=default_dept_date,
        min_value=current_date,
        format="YYYY-MM-DD",
        key="departure_date_picker",
    )
    is_return_trip = st.checkbox("Return Trip?", value=True, key="return_trip_toggle")
    return_date = None
    if is_return_trip:
        return_date = st.date_input(
            "Return Date:",
            value=default_ret_date,
            min_value=departure_date,
            format="YYYY-MM-DD",
            key="return_date_picker",
        )
    trigger_execution = st.button(
        "🔎 Execute Crawler", type="primary", use_container_width=True
    )

results_container = st.container()
with results_container:
    st.subheader("📋 Selected Parameters")
    param_col_1, param_col_2 = st.columns(2)
    with param_col_1:
        st.info(f"**Airline (Config Key)**: `{selected_crawler_key}`")
        st.info(f"**Route**: `{origin_iata_code}` → `{destination_iata_code}`")
    with param_col_2:
        st.info(f"**Departure Date**: `{departure_date.strftime('%Y-%m-%d')}`")
        st.info(
            f"**Return Date**: `{return_date.strftime('%Y-%m-%d') if is_return_trip and return_date else '*One-way trip*'}`"
        )

    if trigger_execution:
        can_proceed = True
        if not (origin_iata_code and is_valid_iata_code(origin_iata_code)):
            st.error("Invalid Origin IATA.")
            can_proceed = False
        if not (destination_iata_code and is_valid_iata_code(destination_iata_code)):
            st.error("Invalid Destination IATA.")
            can_proceed = False
        if origin_iata_code == destination_iata_code and origin_iata_code:
            st.error("Origin and Destination can't be same.")
            can_proceed = False
        if can_proceed:
            st.markdown("---")
            st.subheader("🚀 Execution Status")
            departure_date_as_str = departure_date.strftime("%Y-%m-%d")
            return_date_as_str = (
                return_date.strftime("%Y-%m-%d")
                if is_return_trip and return_date
                else None
            )
            with st.spinner(f"Executing crawler for '{selected_crawler_key}'..."):
                is_success, status_message, result_df = run_crawler_task(
                    selected_crawler_key,
                    origin_iata_code,
                    destination_iata_code,
                    departure_date_as_str,
                    return_date_as_str,
                )
            if is_success:
                st.success(status_message)
                if result_df is not None and not result_df.empty:
                    st.write("📊 Extracted Data Overview:")
                    st.dataframe(result_df, height=350, use_container_width=True)
                elif result_df is not None:
                    st.info("Crawler ran, but no data extracted.")
            else:
                st.error(status_message)
        else:
            st.warning("Correct parameters before execution.")

with st.expander("ℹ️ About This Dynamic Crawler", expanded=False):
    st.markdown(
        """
    This application executes a dynamic web scraper for flight data.
    - Configurations are loaded from JSONs in **Redis**.
    - Uses **IATA codes** for airports.
    - Data saved to **MongoDB**.
    - Logs in console and `logs/streamlit_app.log`.
    """
    )
    st.caption("Designed for flexibility.")
