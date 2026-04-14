"""
extractor.py - Rule-based fallback intent extraction
"""

from typing import List
from .constants import ENTITY_MAPPINGS, ATTRIBUTE_MAPPINGS, TASK_KEYWORDS, SYSTEM_KEYWORDS
from .normalizer import IntentNormalizer
from .utils import infer_priority, compute_confidence


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
    
    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """Extract entity mentions"""
        text_lower = text.lower()
        entities = []
        for entity in ENTITY_MAPPINGS.keys():
            if entity in text_lower:
                normalized = ENTITY_MAPPINGS[entity]
                if normalized not in entities:
                    entities.append(normalized)
        return entities if entities else ["payroll"]  # default
    
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
    
    @staticmethod
    def extract_systems(text: str) -> List[str]:
        """
        Improved system detection logic
        Smart inference instead of loose defaults
        """
        text_lower = text.lower()
        systems = []
        
        for system, keywords in SYSTEM_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                systems.append(system)
        
        # Smart fallback - avoid loose defaults
        if not systems:
            # If mentions API/REST/HTTP then Unisys
            if any(kw in text_lower for kw in ["api", "rest", "http", "service"]):
                return ["unisys"]
            # If mentions datasets/JCL/Zowe then IBM
            elif any(kw in text_lower for kw in ["dataset", "jcl", "zowe", "job"]):
                return ["ibm"]
            # Default to IBM (mainframe-first architecture)
            else:
                return ["ibm"]
        
        return systems
