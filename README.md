# Product Deals Scraper

A powerful web scraping application that aggregates product deals from local Dominican Republic e-commerce websites. The application features natural language search capabilities and intelligent filtering to help users find the best deals on electronics and appliances.

## Features

- **Intelligent Search**: Natural language processing for intuitive product search
- **Multiple Sources**: Scrapes deals from multiple websites:
  - electrodomesticos.com.do
  - plazalama.com.do
- **Smart Filtering**: Filter results by:
  - Category (TV, Phone, Laptop, etc.)
  - Brand (Samsung, Apple, LG, etc.)
  - Price Range
  - Condition (New/Used)
  - Location
- **Stealth Scraping**: Built-in protection against anti-bot measures
- **Modular Design**: Easy to extend with additional websites
- **Clean Data**: Well-structured JSON output

## Installation

1. Clone the repository:

```bash
git clone [repository-url]
cd products_scraper_playwright
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:

```bash
playwright install
```

## Usage

1. Basic usage:

```python
python main.py
```

2. With custom filters:

```python
filters = {
    "category": "TV",
    "brand": ["Samsung", "LG"],
    "price_range": {"min": 10000, "max": 50000},
    "condition": "New",
    "location": "Santo Domingo"
}
```

## Project Structure

```
products_scraper_playwright/
├── core/                      # Core functionality
│   ├── base_scraper.py       # Base scraper class
│   ├── data_models.py        # Data models/schemas
│   ├── request_manager.py    # HTTP request handling
│   ├── search.py            # Search functionality
│   └── utils.py             # Utility functions
├── scrapers/                 # Site-specific scrapers
│   ├── electrodomesticos.py
│   └── plazalama.py
├── pipelines/               # Data processing
│   ├── cleaning.py         # Data cleaning
│   └── storage.py          # Data storage
└── main.py                 # Entry point
```

## Adding New Scrapers

To add a new website scraper:

1. Create a new file in the `scrapers/` directory
2. Extend the `BaseScraper` class
3. Implement the required methods:
   - `scrape()`
   - `get_supported_filters()`

Example:

```python
from core.base_scraper import BaseScraper

class NewSiteScraper(BaseScraper):
    async def scrape(self, filters):
        # Implementation here
        pass

    @staticmethod
    def get_supported_filters():
        return {
            "category": ["TV", "Phone"],
            "brand": ["Samsung", "LG"],
            # ...
        }
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
