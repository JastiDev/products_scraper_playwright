from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from core.data_models import DealItem
from core.request_manager import RequestManager

class BaseScraper(ABC):
    def __init__(self, request_manager: Optional[RequestManager] = None):
        self.request_manager = request_manager or RequestManager()
    
    @abstractmethod
    async def scrape(self, filters: Dict) -> List[DealItem]:
        """Main scraping method to be implemented by each site scraper"""
        pass

    @staticmethod
    @abstractmethod
    def get_supported_filters() -> Dict:
        """Return supported filters for this scraper"""
        pass