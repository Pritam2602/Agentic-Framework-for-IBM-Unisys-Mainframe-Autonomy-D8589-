"""
extractor.py - Rule-based fallback intent extraction

CRITICAL RULES:
1. ENTITY vs FILTER: Entities are objects, identifiers are FILTERS
2. SYSTEM OWNERSHIP: Respect entity-system mapping
3. ENTITY PRIORITY: shopping > transaction > account > customer
"""

from typing import List, Dict, Any
from .constants import (
    ENTITY_MAPPINGS, 
    ATTRIBUTE_MAPPINGS, 
    TASK_KEYWORDS, 
    SYSTEM_KEYWORDS,
    ENTITY_SYSTEM_MAPPING,
    ENTITY_PRIORITY
)
from .normalizer import IntentNormalizer


class RuleBasedExtractor:
    """Fallback rule-based intent extraction when LLM fails"""
    
    def __init__(self):
        self.normalizer = IntentNormalizer()
    
    @staticmethod
    def extract_task(text: str) -> str:
        """Infer task from keywords"""
        text_lower = text.lower()
        for task, keywords in TASK_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return task
        return "fetch"  # default
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract entity mentions (BUSINESS OBJECTS ONLY)
        
        CRITICAL: Identifiers like "customer" are FILTERS, not entities
        Only extract shopping, transaction, account as entities
        """
        text_lower = text.lower()
        entities = []
        
        for entity_key in ENTITY_MAPPINGS.keys():
            if entity_key in text_lower:
                normalized = ENTITY_MAPPINGS[entity_key]
                if normalized not in entities:
                    entities.append(normalized)
        
        # Apply CRITICAL RULE 3: Entity Priority
        entities = self.normalizer.apply_entity_priority(entities)
        
        return entities if entities else ["shopping"]  # default to shopping
    
    @staticmethod
    def extract_attributes(text: str) -> List[str]:
        """Extract attribute mentions"""
        text_lower = text.lower()
        attributes = []
        for attr in ATTRIBUTE_MAPPINGS.keys():
            if attr in text_lower:
                normalized = ATTRIBUTE_MAPPINGS[attr]
                if normalized not in attributes:
                    attributes.append(normalized)
        return attributes
    
    def extract_systems(self, text: str, entities: List[str]) -> List[str]:
        """
        Extract systems based on:
        1. Explicit system mentions (IBM, Unisys keywords)
        2. Entity-to-system mapping (CRITICAL RULE 2)
        
        System Ownership:
        - shopping -> Unisys
        - transaction -> IBM
        - account -> IBM
        - customer -> IBM
        """
        text_lower = text.lower()
        systems = set()
        
        # First: Check explicit system mentions
        for system, keywords in SYSTEM_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                systems.add(system)
        
        # Second: Map entities to systems (CRITICAL RULE 2)
        for entity in entities:
            if entity in ENTITY_SYSTEM_MAPPING:
                systems.add(ENTITY_SYSTEM_MAPPING[entity])
        
        # Default: If no entities match and no explicit mention, use IBM
        if not systems:
            systems.add("ibm")
        
        return list(systems)
    
    def extract_filters(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract filter conditions as structured {field, value} pairs
        
        CRITICAL RULE 1: Filters contain identifiers and conditions
        NOT entity names
        """
        return self.normalizer.extract_filters(text)

    def extract_metric(self, text: str) -> str | None:
        """Extract requested business metric if present."""
        return self.normalizer.extract_metric(text)

    def extract_aggregation(self, text: str) -> str | None:
        """Extract requested aggregation function if present."""
        return self.normalizer.extract_aggregation(text)
