import json
from datetime import datetime
from typing import Dict, List
from core.data_models import DealItem

def save_to_json(data: Dict[str, List[DealItem]], filename: str):
    serializable_data = {}
    for site, items in data.items():
        serializable_data[site] = [item.dict() for item in items]
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_deals": sum(len(v) for v in data.values())
            },
            "data": serializable_data
        }, f, ensure_ascii=False, indent=2)