"""
normalizer.py - Intent normalization logic
"""

import re
from typing import Dict, Optional
from datetime import datetime, timedelta
from .constants import ENTITY_MAPPINGS, ATTRIBUTE_MAPPINGS


class IntentNormalizer:
    """Normalize intent outputs (dates, entity names, attributes, etc.)"""
    
    @staticmethod
    def normalize_entity(text: str) -> str:
        """Map entity synonyms to canonical names"""
        text_lower = text.lower().strip()
        return ENTITY_MAPPINGS.get(text_lower, text)
    
    @staticmethod
    def normalize_attribute(text: str) -> str:
        """Map attribute synonyms to canonical names"""
        text_lower = text.lower().strip()
        return ATTRIBUTE_MAPPINGS.get(text_lower, text)
    
    @staticmethod
    def normalize_date_range(text: str) -> Optional[Dict[str, str]]:
        """Extract and normalize date ranges"""
        text_lower = text.lower().strip()
        
        # Parse month/year
        month_year_match = re.search(
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
            text_lower
        )
        if month_year_match:
            month_name, year = month_year_match.groups()
            month = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }[month_name]
            year = int(year)
            
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = datetime(year, month + 1, 1) - timedelta(days=1)
            
            return {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }
        
        # Parse "last N days"
        days_match = re.search(r'last\s+(\d+)\s+days?', text_lower)
        if days_match:
            days = int(days_match.group(1))
            end = datetime.now()
            start = end - timedelta(days=days)
            return {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }
        
        # Parse explicit date range
        date_range_match = re.search(
            r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})',
            text_lower
        )
        if date_range_match:
            return {
                "start": date_range_match.group(1),
                "end": date_range_match.group(2)
            }
        
        return None
