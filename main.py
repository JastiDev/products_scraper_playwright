import asyncio
import json
import os
import sys
from typing import List, Dict, Any, Union
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from scrapers.electrodomesticos import ElectrodomesticosScraper
from scrapers.plazalama import PlazaLamaScraper
from core.data_models import DealItem, Condition
from pipelines.cleaning import clean_data
from pipelines.storage import save_to_json
from loguru import logger

# Configure logger
logger.add(
    "scraper.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
    rotation="1 day"
)

SCRAPERS = {
    "electrodomesticos": ElectrodomesticosScraper,
    "plazalama": PlazaLamaScraper
}

async def scrape_all(filters: Dict) -> Dict[str, List[DealItem]]:
    results = {}
    
    for site_name, scraper_class in SCRAPERS.items():
        scraper = None
        try:
            scraper = scraper_class()
            if not _filters_are_supported(scraper, filters):
                logger.warning(f"Filters are not supported for {site_name}")
                continue
                
            site_results = await scraper.scrape(filters)
            logger.info(f"Scraped {len(site_results)} deals from {site_name}")
            results[site_name] = clean_data(site_results)
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {str(e)}", exc_info=True)
            continue
        finally:
            if scraper and scraper.request_manager:
                await scraper.request_manager.close()
    
    return results

def _filters_are_supported(scraper, filters: Dict) -> bool:
    supported = scraper.get_supported_filters()
    
    for key, value in filters.items():
        # Check if the filter key is supported
        if key not in supported:
            logger.warning(f"Filter {key} is not supported for {scraper.__class__.__name__}")
            return False
            
        supported_value = supported[key]
        
        # Handle price_range dictionary
        if key == "price_range":
            if not isinstance(value, dict):
                logger.warning(f"Price range must be a dictionary for {scraper.__class__.__name__}")
                return False
            continue
            
        # Handle list of values (e.g., brands)
        if isinstance(supported_value, list):
            # Convert single value to list for uniform handling
            filter_values = value if isinstance(value, list) else [value]
            
            # Check if all provided values are supported
            for val in filter_values:
                if val not in supported_value:
                    logger.warning(f"Value {val} not in supported values {supported_value} for filter {key} in {scraper.__class__.__name__}")
                    return False
                    
        # Handle other types of values
        elif value != supported_value and supported_value != Any:
            logger.warning(f"Unsupported value {value} for filter {key} in {scraper.__class__.__name__}")
            return False
            
    return True

async def main():
    try:
        # Ensure we're in the project root directory
        os.chdir(project_root)
        
        filters = {
            "brand": ["Samsung"],  # Now supports list of brands
            "price_range": {"min": 10000, "max": 50000},
            "condition": "New",  # Changed from "NEW" to "New"
            "location": "Santo Domingo"
        }
        
        logger.info("Starting scraping process...")
        results = await scrape_all(filters)
        
        output_file = "deals_output.json"
        save_to_json(results, output_file)
        logger.info(f"Results saved to {output_file}")
        logger.info(f"Scraped {sum(len(v) for v in results.values())} deals in total")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())