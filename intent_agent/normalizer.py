"""
normalizer.py - Intent normalization logic

CRITICAL: 
- Entities are business objects
- Filters are field-value conditions
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from .constants import (
    ENTITY_MAPPINGS,
    ATTRIBUTE_MAPPINGS,
    IDENTIFIER_MAPPINGS,
    ENTITY_PRIORITY,
    METRIC_KEYWORDS,
    AGGREGATION_KEYWORDS,
    ENTITY_SYSTEM_MAPPING,
)


class IntentNormalizer:
    """Normalize intent outputs (dates, entity names, attributes, filters)"""
    
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
    def extract_metric(text: str) -> Optional[str]:
        """Infer requested business metric from the query text."""
        text_lower = text.lower()
        for metric, phrases in METRIC_KEYWORDS.items():
            if any(phrase in text_lower for phrase in phrases):
                return metric

        if "spend" in text_lower:
            return "total_spend" if IntentNormalizer.extract_aggregation(text) == "sum" else "spend"

        return None

    @staticmethod
    def extract_aggregation(text: str) -> Optional[str]:
        """Infer aggregate operation such as sum, avg, or count."""
        text_lower = text.lower()
        for aggregation, phrases in AGGREGATION_KEYWORDS.items():
            if any(phrase in text_lower for phrase in phrases):
                return aggregation
        return None

    @staticmethod
    def infer_output_mode(text: str, task: str, aggregation: Optional[str]) -> str:
        """Determine if the user expects raw records, an aggregate, or an insight."""
        text_lower = text.lower()
        if task == "discover" or IntentNormalizer.is_capability_discovery(text):
            return "capabilities"
        if aggregation:
            return "aggregate"
        if task == "analyze" or any(keyword in text_lower for keyword in ["trend", "insight", "summary"]):
            return "insight"
        return "records"

    @staticmethod
    def is_capability_discovery(text: str) -> bool:
        """Detect requests asking whether related data/capabilities exist."""
        text_lower = text.lower()
        discovery_phrases = [
            "discover",
            "discovery",
            "available",
            "availability",
            "exists",
            "exist",
            "check whether",
            "check if",
            "what else",
            "what other",
            "related data",
            "capability",
            "capabilities",
            "what is possible",
            "what's possible",
        ]
        return any(phrase in text_lower for phrase in discovery_phrases)

    @staticmethod
    def infer_federation_requirement(
        entities: List[str],
        systems: List[str],
        metric: Optional[str],
        aggregation: Optional[str],
    ) -> bool:
        """Estimate whether the request likely needs more than one system."""
        if len(systems) > 1:
            return True
        entity_systems = {
            ENTITY_SYSTEM_MAPPING.get(entity)
            for entity in entities
            if ENTITY_SYSTEM_MAPPING.get(entity)
        }
        if len(entity_systems) > 1:
            return True
        if aggregation and len(systems) > 1:
            return True
        return False

    @staticmethod
    def needs_behavioral_enrichment(text: str) -> bool:
        """Detect if the user explicitly wants shopping/behavioral context."""
        text_lower = text.lower()
        enrichment_signals = [
            "shopping",
            "behavior",
            "behavioral",
            "merchant",
            "category",
            "loyalty",
            "browsing",
            "cart",
            "eportal",
            "unisys",
        ]
        return any(signal in text_lower for signal in enrichment_signals)
    
    @staticmethod
    def apply_entity_priority(entities: List[str]) -> List[str]:
        """Apply entity priority rule: shopping > transaction > account"""
        # Filter to only entities that exist in priority list
        prioritized = [e for e in ENTITY_PRIORITY if e in entities]
        # Add remaining entities not in priority
        remaining = [e for e in entities if e not in ENTITY_PRIORITY]
        return prioritized + remaining
    
    @staticmethod
    def extract_filters(text: str) -> List[Dict[str, Any]]:
        """
        Extract filter conditions as {field, value} pairs
        
        Examples:
        - "customer 101" -> {field: customerId, value: 101}
        - "on 2026-03-10" -> {field: date, value: 2026-03-10}
        """
        filters = []
        text_lower = text.lower()
        
        # Pattern 1: "customer/account/merchant <id number>"
        for key, field in IDENTIFIER_MAPPINGS.items():
            patterns = [
                rf'\b{re.escape(key)}\s+(\d+)',  # "customer 101"
                rf'\b{re.escape(key)}[:\s=]+(\d+)',  # "customer: 101" or "customer=101"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                for value in matches:
                    filters.append({
                        "field": field,
                        "value": int(value) if value.isdigit() else value
                    })
        
        # Pattern 2: Explicit dates
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        for date_value in re.findall(date_pattern, text):
            filters.append({"field": "date", "value": date_value})

        known_categories = [
            "electronics", "food", "travel", "fashion",
            "grocery", "entertainment", "beauty", "fitness",
        ]
        for category in known_categories:
            if re.search(rf"\b{re.escape(category)}\b", text_lower):
                filters.append({"field": "category", "value": category})
                break

        known_merchants = [
            "amazon", "flipkart", "swiggy", "zomato", "uber", "myntra",
            "bigbasket", "makemytrip", "croma", "bookmyshow", "nykaa",
            "decathlon",
        ]
        for merchant in known_merchants:
            if re.search(rf"\b{re.escape(merchant)}\b", text_lower):
                filters.append({"field": "merchant", "value": merchant})
                break
        
        return filters
    
    @staticmethod
    def normalize_date_range(text: str) -> Optional[Dict[str, str]]:
        """Extract and normalize date ranges"""
        text_lower = text.lower().strip()
        
        # Parse explicit date "YYYY-MM-DD"
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text_lower)
        if date_match:
            date_str = date_match.group(1)
            return {"start": date_str, "end": date_str}
        
        # Parse month/year "March 2026"
        month_year_match = re.search(
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',
            text_lower
        )
        if month_year_match:
            month_name, year = month_year_match.groups()
            month_map = {
                "january": 1, "february": 2, "march": 3, "april": 4,
                "may": 5, "june": 6, "july": 7, "august": 8,
                "september": 9, "october": 10, "november": 11, "december": 12
            }
            month = month_map[month_name]
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
        days_match = re.search(r"last\s+(\d+)\s+days?", text_lower)
        if days_match:
            days = int(days_match.group(1))
            end = datetime.now()
            start = end - timedelta(days=days)
            return {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }
        
        # Parse "last week", "yesterday", "today"
        if "today" in text_lower or "today" in text_lower:
            today = datetime.now()
            return {"start": today.strftime("%Y-%m-%d"), "end": today.strftime("%Y-%m-%d")}
        
        if "yesterday" in text_lower:
            yesterday = datetime.now() - timedelta(days=1)
            return {"start": yesterday.strftime("%Y-%m-%d"), "end": yesterday.strftime("%Y-%m-%d")}
        
        if "last week" in text_lower:
            end = datetime.now()
            start = end - timedelta(days=7)
            return {
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d")
            }
        
        return None
