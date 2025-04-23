from core.data_models import DealItem
from typing import List
import re

def clean_data(items: List[DealItem]) -> List[DealItem]:
    cleaned = []
    for item in items:
        try:
            # Clean title
            item.title = re.sub(r"\s+", " ", item.title).strip()
            
            # Standardize brand names
            item.brand = _standardize_brand(item.brand)
            
            # Validate and clean other fields
            cleaned.append(item)
        except Exception as e:
            continue
    return cleaned

def _standardize_brand(brand: str) -> str:
    brand = brand.strip().title()
    mappings = {
        "Samsung": ["Samsung", "Smg"],
        "LG": ["LG", "Lg", "Elgie"],
        # Add more brand mappings
    }
    for std_brand, variants in mappings.items():
        if brand in variants:
            return std_brand
    return brand