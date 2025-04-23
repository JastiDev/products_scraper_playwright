from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime
import re

class Category(str, Enum):
    TV = "TV"
    PHONE = "Phone"
    LAPTOP = "Laptop"
    FRIDGE = "Fridge"
    WASHING_MACHINE = "Washing Machine"
    AIR_CONDITIONER = "Air Conditioner"
    MICROWAVE = "Microwave"
    STOVE = "Stove"
    
    @classmethod
    def from_string(cls, value: str) -> "Category":
        """Convert string to category, handling common variations"""
        value = value.lower().strip()
        mapping = {
            "television": cls.TV,
            "smartphone": cls.PHONE,
            "mobile": cls.PHONE,
            "notebook": cls.LAPTOP,
            "refrigerator": cls.FRIDGE,
            "nevera": cls.FRIDGE,
            "lavadora": cls.WASHING_MACHINE,
            "aire acondicionado": cls.AIR_CONDITIONER,
            "microondas": cls.MICROWAVE,
            "estufa": cls.STOVE,
        }
        return mapping.get(value, next((c for c in cls if c.value.lower() == value), None))

class Condition(str, Enum):
    NEW = "New"
    USED = "Used"
    REFURBISHED = "Refurbished"
    
    @classmethod
    def from_string(cls, value: str) -> "Condition":
        """Convert string to condition, handling common variations"""
        value = value.lower().strip()
        mapping = {
            "nuevo": cls.NEW,
            "usado": cls.USED,
            "reacondicionado": cls.REFURBISHED,
            "refurbished": cls.REFURBISHED,
        }
        return mapping.get(value, next((c for c in cls if c.value.lower() == value), None))

class DealItem(BaseModel):
    title: str
    price: float
    original_price: Optional[float] = None
    currency: str = "DOP"
    category: Category
    brand: str
    condition: Condition
    location: str
    url: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, str]] = Field(default_factory=dict)
    features: Optional[List[str]] = Field(default_factory=list)
    availability: bool = True
    seller: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @validator('price', 'original_price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price cannot be negative')
        return v
    
    def to_search_text(self) -> str:
        """Convert item to searchable text for natural language search"""
        search_parts = [
            self.title,
            self.brand,
            self.category.value,
            self.condition.value,
            self.location,
            self.description or "",
        ]
        
        # Add features if they exist
        if self.features:
            search_parts.extend(self.features)
            
        # Add specifications if they exist
        if self.specifications:
            search_parts.extend(f"{k}: {v}" for k, v in self.specifications.items())
            
        return " ".join(filter(None, search_parts)).lower()
    
    def matches_query(self, query: str, filters: Dict = None) -> bool:
        """Check if item matches search query and filters"""
        # Natural language search
        search_text = self.to_search_text()
        if not all(term.lower() in search_text for term in query.split()):
            return False
            
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if key == "price_range":
                    if value.get("min") and self.price < value["min"]:
                        return False
                    if value.get("max") and self.price > value["max"]:
                        return False
                elif key == "brand" and isinstance(value, list):
                    if self.brand not in value:
                        return False
                elif key == "condition" and self.condition != value:
                    return False
                elif key == "location" and value.lower() not in self.location.lower():
                    return False
                elif key == "category" and self.category != value:
                    return False
                    
        return True