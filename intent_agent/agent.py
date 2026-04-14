"""
agent.py - Main IntentAgent class
"""

import json
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from .schemas import IntentOutput, FilterCriteria
from .normalizer import IntentNormalizer
from .extractor import RuleBasedExtractor
from .constants import DEFAULT_ENTITY_ATTRIBUTES
from .utils import infer_priority, compute_confidence


class IntentAgent:
    """
    Production Intent Agent: Pure Understanding Layer
    
    Maps user natural language to structured intent JSON
    Does NOT: commands, APIs, data access, or planning
    """
    
    def __init__(self, model: Any):
        self.model = model
        self.normalizer = IntentNormalizer()
        self.fallback_extractor = RuleBasedExtractor()
        self.prompt = self._build_prompt()
    
    def _build_prompt(self):
        """Build LLM prompt for intent understanding"""
        
        system_prompt = """
You are an enterprise intent-to-structure mapper.

Your ONLY job is to understand WHAT the user wants.

You do NOT:
- Generate commands
- Call APIs
- Plan execution
- Access data

You MUST extract:
1. task: fetch | reconcile | analyze | compare | transform
2. entities: payroll, customer, transaction, account
3. attributes: specific fields needed
4. filters: time ranges, conditions
5. systems: ibm | unisys
6. priority: low | medium | high (high for compare/analyze, medium for fetch)
7. confidence: 0.0 to 1.0 based on clarity

Return STRICT JSON ONLY:

{
  "task": "string",
  "entities": ["string"],
  "attributes": ["string"],
  "filters": {
    "time_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "conditions": ["string"]
  },
  "systems": ["string"],
  "priority": "low|medium|high",
  "confidence_score": 0.0
}

IMPORTANT:
- If task is compare/analyze then priority = high
- If entity is payroll then include common attributes
- Be conservative: if unsure about system, default to IBM
"""
        
        return ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", "{user_input}")
            ]
        )
    
    def run(self, user_prompt: str) -> IntentOutput:
        """
        Process user input and return structured intent.
        Falls back to rule-based extraction if LLM fails.
        """
        
        try:
            chain = self.prompt | self.model
            result = chain.invoke({"user_input": user_prompt})
            return self._parse_and_normalize(result.content)
            
        except Exception as e:
            print(f"[FALLBACK] LLM failed: {e}")
            return self._fallback_extract(user_prompt)
    
    def _parse_and_normalize(self, text: str) -> IntentOutput:
        """
        Extract and validate JSON from LLM output.
        Apply all normalizations and fixes.
        """
        try:
            # Extract JSON
            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                raise ValueError("No JSON found in LLM output")
            
            json_text = json_match.group()
            data = json.loads(json_text)
            
            # FIX 1: Entity Default Attributes
            if "entities" in data:
                data["entities"] = [
                    self.normalizer.normalize_entity(e) for e in data["entities"]
                ]
            
            # If attributes empty, populate from entity defaults
            if not data.get("attributes") or data.get("attributes") == []:
                attrs = []
                for entity in data.get("entities", []):
                    attrs.extend(DEFAULT_ENTITY_ATTRIBUTES.get(entity, []))
                data["attributes"] = list(set(attrs))
            else:
                # Normalize existing attributes
                data["attributes"] = [
                    self.normalizer.normalize_attribute(a) for a in data["attributes"]
                ]
            
            # FIX 3: Priority Logic
            data["priority"] = infer_priority(data.get("task", "fetch"))
            
            # Normalize date range
            if "filters" in data and "time_range" in data["filters"]:
                if isinstance(data["filters"]["time_range"], str):
                    normalized_range = self.normalizer.normalize_date_range(
                        data["filters"]["time_range"]
                    )
                    if normalized_range:
                        data["filters"]["time_range"] = normalized_range
                    else:
                        data["filters"]["time_range"] = None
            
            # FIX 4: Strict Schema Enforcement
            required_fields = ["task", "entities", "systems"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing or empty required field: {field}")
            
            if not isinstance(data.get("entities"), list):
                data["entities"] = [data["entities"]]
            
            if not isinstance(data.get("attributes"), list):
                data["attributes"] = data.get("attributes", [])
            
            if not isinstance(data.get("systems"), list):
                data["systems"] = [data["systems"]]
            
            # FIX 5: Confidence Score
            data["confidence_score"] = compute_confidence(data)
            
            return IntentOutput(**data)
            
        except Exception as e:
            raise RuntimeError(f"JSON validation failed:\n{text}\nError: {e}")
    
    def _fallback_extract(self, text: str) -> IntentOutput:
        """
        Rule-based extraction when LLM fails.
        Applies all fixes to fallback output too.
        """
        
        task = self.fallback_extractor.extract_task(text)
        entities = self.fallback_extractor.extract_entities(text)
        attributes = self.fallback_extractor.extract_attributes(text)
        systems = self.fallback_extractor.extract_systems(text)
        
        # FIX 1: If attributes empty, populate from entity defaults
        if not attributes:
            for entity in entities:
                attributes.extend(DEFAULT_ENTITY_ATTRIBUTES.get(entity, []))
            attributes = list(set(attributes))
        
        # Extract time range
        time_range = self.normalizer.normalize_date_range(text)
        
        # FIX 3: Priority logic
        priority = infer_priority(task)
        
        # FIX 5: Compute confidence
        fallback_data = {
            "task": task,
            "entities": entities,
            "attributes": attributes,
            "filters": {"time_range": time_range, "conditions": []},
            "systems": systems,
            "priority": priority
        }
        confidence = compute_confidence(fallback_data)
        confidence *= 0.8  # penalize fallback
        
        return IntentOutput(
            task=task,
            entities=entities,
            attributes=attributes,
            filters=FilterCriteria(
                time_range=time_range,
                conditions=[]
            ),
            systems=systems,
            priority=priority,
            confidence_score=confidence
        )
