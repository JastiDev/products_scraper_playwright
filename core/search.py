from typing import List, Dict, Optional
from core.data_models import DealItem
import re
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SearchEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.items: List[DealItem] = []
        self.item_vectors = None
        
    def add_items(self, items: List[DealItem]):
        """Add items to the search index"""
        self.items = items
        texts = [item.to_search_text() for item in items]
        self.item_vectors = self.vectorizer.fit_transform(texts)
        
    def search(self, query: str, filters: Optional[Dict] = None, limit: int = 50) -> List[DealItem]:
        """Search items using natural language query and optional filters"""
        if not self.items:
            return []
            
        # Transform query
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores
        similarities = cosine_similarity(query_vector, self.item_vectors).flatten()
        
        # Get top matches
        matches = []
        for idx, score in enumerate(similarities):
            item = self.items[idx]
            if score > 0.1:  # Minimum similarity threshold
                if not filters or item.matches_query("", filters):  # Apply filters if provided
                    matches.append((score, item))
                    
        # Sort by relevance and return top results
        matches.sort(reverse=True, key=lambda x: x[0])
        return [item for score, item in matches[:limit]]
    
    def get_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        if not self.items or len(partial_query) < 2:
            return []
            
        # Extract common phrases from items matching partial query
        matching_texts = []
        for item in self.items:
            text = item.to_search_text()
            if partial_query.lower() in text:
                matching_texts.append(text)
                
        # Extract frequent phrases
        phrases = defaultdict(int)
        for text in matching_texts:
            words = text.split()
            for i in range(len(words)):
                for j in range(i + 1, min(i + 4, len(words) + 1)):
                    phrase = " ".join(words[i:j])
                    if partial_query.lower() in phrase.lower():
                        phrases[phrase] += 1
                        
        # Return top suggestions
        suggestions = sorted(phrases.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, count in suggestions[:10]] 