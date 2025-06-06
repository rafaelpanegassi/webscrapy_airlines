# Airline Web Scraping Pipeline

This repository hosts an end-to-end project designed for automated web scraping of airline ticket prices. The pipeline is designed to collect, process, and analyze flight pricing data from multiple airlines.

## How it Works

1. **Configuration Setup:** The system uses JSON configuration files to define the scraping rules for each airline.
2. **Web Scraping:** The crawler navigates through airline websites using predefined steps and extracts flight information.
3. **Data Processing:** Extracted data is structured and normalized for consistent analysis.
4. **Data Visualization:** A Streamlit interface provides interactive visualization of flight prices and trends.
5. **Data Storage:** All collected information is systematically stored for historical analysis and price tracking.

## Architecture Details

1. **SOURCE**
    - **Configuration Files:** JSON files containing website navigation rules and data extraction patterns.
    - **Airline Websites:** The source of flight pricing data (e.g., LATAM Airlines).
    - **Web Crawler:** Python-based crawler that handles website navigation and data extraction.

2. **EXTRACT**
    - **Generic Crawler:** A flexible crawler system that can adapt to different airline websites.
    - **Tools Module:** Contains utility functions and helpers for web scraping.
    - **Selenium/Playwright:** Browser automation tools for navigating dynamic websites.

3. **TRANSFORM**
    - **Data Processing:** Standardization of extracted data across different airlines.
    - **Price Normalization:** Consistent handling of currency and pricing information.
    - **Data Validation:** Ensuring data quality and completeness.

4. **VISUALIZATION**
    - **Streamlit Interface:** Interactive dashboard for viewing flight prices.
    - **Price Comparison:** Tools for comparing prices across different airlines.
    - **Historical Tracking:** Visualization of price trends over time.

## How to Run This Project

### Prerequisites
- Python 3.x
- Web browser (Chrome/Firefox)
- Required browser drivers
- Poetry (for dependency management)

### Setup Instructions

1. **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/webscrapy_airlines.git
    cd webscrapy_airlines
    ```

2. **Install Dependencies**
    ```bash
    poetry install
    ```

3. **Configure Environment**
    - Create a `.env` file with necessary configurations
    ```
    BROWSER_TYPE=chrome
    HEADLESS_MODE=true
    LOG_LEVEL=INFO
    ```

4. **Run the Application**
    ```bash
    poetry run streamlit run src/streamlit_app.py
    ```

### Project Structure
```
webscrapy_airlines/
├── src/
│   ├── crawler/           # Specific airline crawlers
│   ├── tools/             # Utility functions
│   ├── generic_crawler.py # Base crawler implementation
│   ├── main_script.py    # Main execution script
│   └── streamlit_app.py  # Web interface
├── steps_scripts/        # Airline-specific JSON configurations
└── README.md
```

### Configuration Files

The project uses JSON configuration files to define scraping behavior. Example structure:

```json
{
    "description": "Airline Configuration",
    "script": {
        "before": {
            "steps": [...]
        },
        "main": {
            "steps": [...]
        },
        "after": {
            "steps": [...]
        }
    },
    "tag": {
        "result_group": {
            "elements": {
                // Data extraction patterns
            }
        }
    }
}
```

### Features

- **Multi-Airline Support:** Extensible architecture for adding new airlines
- **Configurable Scraping:** JSON-based configuration for easy maintenance
- **Interactive Dashboard:** Real-time price visualization
- **Automated Navigation:** Handles cookies, popups, and dynamic content
- **Data Extraction:** Structured extraction of flight details including:
  - Airline name
  - Flight times
  - Airport codes
  - Price information
  - Duration
  - Stop information

### Best Practices

1. **Rate Limiting:** Respectful crawling with appropriate delays
2. **Error Handling:** Robust error management for website changes
3. **Data Validation:** Comprehensive checking of extracted data
4. **Configuration Management:** Separate configuration from code
5. **Modular Design:** Easy to extend for new airlines

### Future Improvements

- **Price Alerts:** Implement notification system for price changes
- **Additional Airlines:** Expand coverage to more carriers
- **Advanced Analytics:** Add predictive pricing models
- **API Integration:** Create REST API for data access
- **Automated Testing:** Add comprehensive test suite
- **Containerization:** Docker support for easy deployment
- **Caching System:** Implement intelligent caching for faster results
- **Multi-Currency Support:** Add currency conversion capabilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.