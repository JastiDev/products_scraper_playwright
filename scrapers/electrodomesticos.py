import os
import sys
from pathlib import Path

# Add the project root directory to Python path when running this file directly
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.absolute()
    sys.path.insert(0, str(project_root))

from core.base_scraper import BaseScraper
from core.data_models import DealItem, Category, Condition
from typing import Dict, List, Union
import re
from bs4 import BeautifulSoup
import logging
import asyncio

class ElectrodomesticosScraper(BaseScraper):
    BASE_URL = "https://electrodomesticos.com.do"
    SUPPORTED_BRANDS = ["Samsung", "LG", "Whirlpool", "Mabe", "Frigidaire", "JVC", "Sony"]
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # Set debug level for detailed logging
        self.logger.setLevel(logging.DEBUG)
        
    @staticmethod
    def get_supported_filters() -> Dict:
        return {
            "category": [c.value for c in Category],
            "brand": ElectrodomesticosScraper.SUPPORTED_BRANDS,
            "price_range": {"min": 0, "max": float("inf")},
            "condition": [c.value for c in Condition],
            "location": ["Santo Domingo", "Santiago", "La Romana"]
        }
    
    async def scrape(self, filters: Dict) -> List[DealItem]:
        results = []
        
        try:
            # Build URL based on category only
            url = self._build_url(filters)
            self.logger.info(f"Starting scrape for URL: {url}")
            
            page = await self.request_manager.get(url)
            self.logger.debug("Page fetched successfully")
            
            # Get the page content and log it for debugging
            content = await page.content()
            self.logger.debug(f"Page content length: {len(content)}")
            self.logger.debug(f"First 1000 characters of content: {content[:1000]}")
            
            # Check if we're being redirected or blocked
            current_url = page.url
            self.logger.debug(f"Current URL after load: {current_url}")
            
            # Take a screenshot for debugging
            await page.screenshot(path="debug_screenshot.png")
            self.logger.debug("Screenshot saved as debug_screenshot.png")
            
            soup = BeautifulSoup(content, 'html.parser')
            self.logger.debug("HTML parsed with BeautifulSoup")
            
            # Log all div classes to help identify the correct selectors
            all_divs = soup.find_all('div', class_=True)
            self.logger.debug("Found divs with classes:")
            for div in all_divs:
                self.logger.debug(f"Div class: {div.get('class')}")
            
            # Find all product items
            products = soup.find_all('div', class_='product-thumb')
            self.logger.info(f"Found {len(products)} products with class 'product-thumb'")
            
            if not products:
                # Try alternative class names that might be present
                self.logger.debug("No products found with 'product-thumb', trying alternative selectors...")
                products = soup.find_all('div', class_='item-product')
                self.logger.debug(f"Found {len(products)} products with class 'item-product'")
                if not products:
                    products = soup.find_all('div', class_='product-item')
                    self.logger.debug(f"Found {len(products)} products with class 'product-item'")
            
            for idx, product in enumerate(products, 1):
                try:
                    self.logger.debug(f"Processing product {idx}/{len(products)}")
                    self.logger.debug(f"Product HTML: {product}")
                    
                    item = self._parse_product(product)
                    self.logger.debug(f"Parsed product: {item}")
                    
                    if self._matches_filters(item, filters):
                        self.logger.debug(f"Product matches filters, adding to results")
                        results.append(item)
                    else:
                        self.logger.debug(f"Product did not match filters")
                except Exception as e:
                    self.logger.error(f"Error parsing product {idx}: {str(e)}")
                    self.logger.error(f"Product HTML that caused error: {product}")
                    continue
            
            await page.close()
            self.logger.info(f"Scraping completed. Found {len(results)} matching products")
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}", exc_info=True)
            
        return results
    
    def _build_url(self, filters: Dict) -> str:
        """Build URL based on filters"""
        url = self.BASE_URL
        
        if "category" in filters:
            category_path = self._get_category_path(filters["category"])
            if category_path:
                url += category_path
                
        return url
    
    def _get_category_path(self, category: str) -> str:
        """Map category to website path"""
        category_paths = {
            "TV": "/electronicos/tv-y-video",
            "PHONE": "/electronicos/celulares",
            "LAPTOP": "/electronicos/computadoras",
            "FRIDGE": "/cocina/refrigeradores",
            "WASHING_MACHINE": "/lavado/lavadoras",
            "AIR_CONDITIONER": "/aires-y-abanicos/aires-acondicionados",
            "MICROWAVE": "/cocina/microondas",
            "STOVE": "/cocina/estufas"
        }
        return category_paths.get(category, "")
    
    def _parse_product(self, product_elem) -> DealItem:
        """Extract product information from HTML element"""
        self.logger.debug("Starting product parsing")
        
        # Get title from h3 tag
        title_elem = product_elem.find('h3')
        if not title_elem:
            self.logger.debug("No h3 tag found, trying alternative title selectors")
            title_elem = product_elem.find('div', class_='name')
            if title_elem:
                title_elem = title_elem.find('a')
        
        title = title_elem.text.strip() if title_elem else ""
        self.logger.debug(f"Found title: {title}")
        
        # Get model number from short-desc
        model_elem = product_elem.find('div', class_='short-desc')
        model = model_elem.text.strip() if model_elem else ""
        self.logger.debug(f"Found model: {model}")
        
        # Get price with detailed logging
        price = 0.0
        price_elem = product_elem.find('span', class_='price')
        if price_elem:
            price_text = price_elem.text.strip()
            self.logger.debug(f"Raw price text: {price_text}")
            # Remove currency symbol (RD$) and convert to float
            price_clean = re.sub(r'[^\d.]', '', price_text)
            self.logger.debug(f"Cleaned price text: {price_clean}")
            try:
                price = float(price_clean)
                self.logger.debug(f"Converted price: {price}")
            except ValueError as e:
                self.logger.error(f"Error converting price '{price_clean}' to float: {str(e)}")
        else:
            self.logger.debug("No price element found")
            
        # Get brand with detailed logging
        brand = ""
        if model:
            brand = model.split()[0]
            self.logger.debug(f"Brand extracted from model: {brand}")
        elif title:
            brand = title.split(',')[0].strip()
            self.logger.debug(f"Brand extracted from title: {brand}")
            
        # Get product URL with validation
        url = ""
        for url_class in ['more-info', 'thumb', 'product-link']:
            url_elem = product_elem.find('a', class_=url_class)
            if url_elem:
                url = url_elem.get('href', '')
                self.logger.debug(f"Found URL with class '{url_class}': {url}")
                break
        
        if not url:
            # Try finding any link that contains the product URL
            url_elem = product_elem.find('a', href=True)
            if url_elem:
                url = url_elem.get('href', '')
                self.logger.debug(f"Found URL from generic link: {url}")
        
        if url and not url.startswith('http'):
            url = self.BASE_URL + url
            self.logger.debug(f"Complete URL: {url}")
            
        # Get image URL with validation
        image_url = None
        img_elem = product_elem.find('img', class_='img-responsive')
        if img_elem:
            image_url = img_elem.get('src', '')
            self.logger.debug(f"Found image URL: {image_url}")
        else:
            self.logger.debug("No image element found")
            
        # Get specifications with detailed logging
        specs = {}
        
        if model:
            specs['model'] = model
            self.logger.debug(f"Added model to specs: {model}")
            
        tax_elem = product_elem.find('span', class_='tax_included_notice')
        if tax_elem:
            specs['tax_info'] = tax_elem.text.strip()
            self.logger.debug(f"Added tax info to specs: {specs['tax_info']}")
            
        if 'Financiable' in product_elem.text:
            specs['financeable'] = True
            self.logger.debug("Product is financeable")
            
        self.logger.debug(f"Final specs: {specs}")
        
        # Infer category from URL or title
        category = self._infer_category(title, url)
        self.logger.debug(f"Inferred category: {category}")
        
        # Create and return DealItem
        item = DealItem(
            title=title,
            price=price,
            category=category,
            brand=brand,
            condition=Condition.NEW,
            location="Santo Domingo",
            url=url,
            image_url=image_url,
            specifications=specs
        )
        self.logger.debug(f"Created DealItem: {item}")
        return item
    
    def _infer_category(self, title: str, url: str) -> Category:
        """Infer product category from title and URL"""
        # First try from URL
        url_lower = url.lower()
        for cat in Category:
            if cat.value.lower() in url_lower:
                return cat
        
        # Then try from title
        title_lower = title.lower()
        category_keywords = {
            Category.TV: ["tv", "televisor", "monitor", "led", "smart tv"],
            Category.PHONE: ["celular", "teléfono", "smartphone"],
            Category.LAPTOP: ["laptop", "computadora", "notebook"],
            Category.FRIDGE: ["nevera", "refrigerador"],
            Category.WASHING_MACHINE: ["lavadora"],
            Category.AIR_CONDITIONER: ["aire acondicionado"],
            Category.MICROWAVE: ["microonda"],
            Category.STOVE: ["estufa", "cocina"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
                
        return Category.TV  # Default category
    
    def _matches_filters(self, item: DealItem, filters: Dict) -> bool:
        """Check if item matches all specified filters"""
        self.logger.debug(f"Checking filters for item: {item.title}")
        self.logger.debug(f"Applied filters: {filters}")
        
        # Brand filter check
        if "brand" in filters:
            brand_filter = filters["brand"]
            # Convert to list if single string
            if isinstance(brand_filter, str):
                brand_filter = [brand_filter]
            
            # Case insensitive brand comparison
            if not any(b.lower() == item.brand.lower() for b in brand_filter):
                self.logger.debug(f"Brand mismatch. Item brand: {item.brand}, Filter brands: {brand_filter}")
                return False
            else:
                self.logger.debug(f"Brand match found for {item.brand}")
                
        if "condition" in filters and item.condition != filters["condition"]:
            self.logger.debug(f"Condition mismatch. Item: {item.condition}, Filter: {filters['condition']}")
            return False
            
        if "location" in filters and filters["location"].lower() not in item.location.lower():
            self.logger.debug(f"Location mismatch. Item: {item.location}, Filter: {filters['location']}")
            return False
            
        if "price_range" in filters:
            min_price = filters["price_range"].get("min")
            max_price = filters["price_range"].get("max")
            if min_price is not None and item.price < min_price:
                self.logger.debug(f"Price below minimum. Item: {item.price}, Min: {min_price}")
                return False
            if max_price is not None and item.price > max_price:
                self.logger.debug(f"Price above maximum. Item: {item.price}, Max: {max_price}")
                return False
                
        self.logger.debug("Item matches all filters")
        return True

# Test code when running this file directly
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test filters
    test_filters = {
        "brand": ["Samsung"],
        "price_range": {"min": 10000, "max": 50000},
        "condition": "NEW",
        "location": "Santo Domingo"
    }
    
    # Create and run scraper
    scraper = ElectrodomesticosScraper()
    results = asyncio.run(scraper.scrape(test_filters))
    
    # Print results
    print(f"\nScraped {len(results)} products:")
    for item in results:
        print(f"\nTitle: {item.title}")
        print(f"Price: {item.price}")
        print(f"Brand: {item.brand}")
        print(f"URL: {item.url}")
        print("-" * 50)