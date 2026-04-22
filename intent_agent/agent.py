"""
agent.py - Main IntentAgent class

CRITICAL RULES:
1. ENTITY vs FILTER: Entities are objects, identifiers are FILTERS
2. SYSTEM OWNERSHIP: shopping->Unisys, transactions->IBM
3. ENTITY PRIORITY: shopping > transactions > customer
4. Filter extraction with {field, value} pairs
5. Confidence scoring based on completeness
"""

import json
import re
from typing import Any, List

from langchain_core.prompts import ChatPromptTemplate

from .schemas import IntentOutput, FilterCriteria, FilterCondition
from .normalizer import IntentNormalizer
from .extractor import RuleBasedExtractor
from .constants import DEFAULT_ENTITY_ATTRIBUTES, ENTITY_SYSTEM_MAPPING
from .utils import infer_priority, compute_confidence


class IntentAgent:
    """
    Production Intent Agent: Pure Understanding Layer
    
    Maps user natural language to structured intent JSON
    Follows CRITICAL RULES for entity/filter distinction and system mapping
    
    Does NOT: commands, APIs, data access, or planning
    """
    
    def __init__(self, model: Any):
        self.model = model
        self.normalizer = IntentNormalizer()
        self.fallback_extractor = RuleBasedExtractor()
        self.prompt = self._build_prompt()
    
    def _build_prompt(self):
        """Build LLM prompt for intent understanding"""
        
        # CRITICAL: Escape curly braces for LangChain template {{ -> { and }} -> }
        system_prompt = """You are an enterprise intent-to-structure mapper for a data federation system.

Your ONLY job is to understand WHAT the user wants.

CRITICAL RULES:
1. ENTITY vs FILTER:
   - Entities are BUSINESS OBJECTS: shopping, transaction, account
   - FILTERS are identifiers/conditions: customerId, date range
   - "customer 101" -> entity=shopping, filter with customerId=101

2. SYSTEM OWNERSHIP:
   - shopping -> Unisys
   - transaction -> IBM
   - account -> IBM

3. ENTITY PRIORITY:
   If multiple entities: shopping > transaction > account

4. TASK DETECTION:
   - fetch -> get/show/list
   - compare -> compare/difference
   - analyze -> trends/insights
   - reconcile -> match/merge
   - transform -> convert/export

5. FILTER EXTRACTION:
   Extract as field-value pairs:
   - "customer 101" -> customerId: 101
   - "on 2026-03-10" -> date: "2026-03-10"

6. METRIC AND AGGREGATION:
   - "total spend" -> metric=total_spend, aggregation=sum, output_mode=aggregate
   - "average spend" -> metric=average_spend, aggregation=avg, output_mode=aggregate
   - If the user asks for totals, counts, or averages, capture that explicitly

Return STRICT JSON ONLY (no markdown, no backticks):

{{
  "task": "fetch|reconcile|analyze|compare|transform",
  "entities": ["shopping", "transaction", "account"],
  "attributes": ["customerId", "merchant", "amount", "date", "category"],
  "filters": {{
    "time_range": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}},
    "conditions": [
      {{"field": "customerId", "value": 101}},
      {{"field": "date", "value": "2026-03-10"}}
    ]
  }},
  "systems": ["unisys", "ibm"],
  "metric": "total_spend|average_spend|transaction_count|null",
  "aggregation": "sum|avg|count|max|min|null",
  "output_mode": "records|aggregate|insight",
  "requires_federation": true,
  "priority": "low|medium|high",
  "confidence_score": 0.0-1.0
}}

NOTES:
- If entity is shopping, include merchant, amount, date, category in attributes
- Priority: high for compare/analyze, medium for fetch, low for others
- If the user asks for "total spend", prefer task=analyze, output_mode=aggregate, metric=total_spend
- Confidence: high (0.8-1.0) if clear, medium (0.5-0.8) if partial, low (<0.5) if unclear
- Always return valid JSON
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
        if self.model is None:
            return self._fallback_extract(user_prompt)

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
        Apply all normalizations and rules.
        """
        try:
            # Extract JSON
            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                raise ValueError("No JSON found in LLM output")
            
            json_text = json_match.group()
            data = json.loads(json_text)
            
            # FIX 1: Entity Default Attributes
            if "entities" in data and data["entities"]:
                data["entities"] = [
                    self.normalizer.normalize_entity(e) for e in data["entities"]
                ]
                # Apply entity priority
                data["entities"] = self.normalizer.apply_entity_priority(data["entities"])
            else:
                data["entities"] = ["shopping"]
            
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
            
            # FIX 2: System Ownership (CRITICAL RULE 2)
            if not data.get("systems"):
                data["systems"] = []
                for entity in data.get("entities", []):
                    if entity in ENTITY_SYSTEM_MAPPING:
                        system = ENTITY_SYSTEM_MAPPING[entity]
                        if system not in data["systems"]:
                            data["systems"].append(system)
                if not data["systems"]:
                    data["systems"] = ["ibm"]  # default
            
            # FIX 3: Priority Logic
            data["priority"] = infer_priority(data.get("task", "fetch"))

            # FIX 3A: Metric / Aggregation / Output Mode
            metric = data.get("metric") or self.normalizer.extract_metric(text)
            aggregation = data.get("aggregation") or self.normalizer.extract_aggregation(text)
            data["metric"] = metric
            data["aggregation"] = aggregation
            data["output_mode"] = self.normalizer.infer_output_mode(
                text,
                data.get("task", "fetch"),
                aggregation,
            )

            if aggregation and data.get("task") == "fetch":
                data["task"] = "analyze"
                data["priority"] = infer_priority(data["task"])

            data["requires_federation"] = self.normalizer.infer_federation_requirement(
                data.get("entities", []),
                data.get("systems", []),
                metric,
                aggregation,
            )

            if data["requires_federation"]:
                for system in ("unisys", "ibm"):
                    if system not in data["systems"]:
                        data["systems"].append(system)

                if metric == "total_spend" and "transaction" not in data["entities"]:
                    data["entities"].append("transaction")
                    data["entities"] = self.normalizer.apply_entity_priority(data["entities"])
                    for attr in DEFAULT_ENTITY_ATTRIBUTES.get("transaction", []):
                        if attr not in data["attributes"]:
                            data["attributes"].append(attr)
            
            # FIX 4: Process Filters
            if "filters" not in data:
                data["filters"] = {}
            
            # Convert filter conditions to FilterCondition objects if needed
            if "conditions" in data["filters"]:
                conditions = data["filters"]["conditions"]
                if conditions and isinstance(conditions[0], dict):
                    # Already in correct format
                    pass
            else:
                data["filters"]["conditions"] = []
            
            # Normalize time_range
            if "time_range" in data["filters"] and data["filters"]["time_range"]:
                if isinstance(data["filters"]["time_range"], str):
                    normalized_range = self.normalizer.normalize_date_range(
                        data["filters"]["time_range"]
                    )
                    data["filters"]["time_range"] = normalized_range
            
            # FIX 5: Strict Schema Enforcement
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
            
            # FIX 6: Confidence Score
            data["confidence_score"] = compute_confidence(data)
            
            # Build FilterCriteria with FilterCondition objects
            filter_conditions = []
            if "conditions" in data.get("filters", {}):
                for cond in data["filters"]["conditions"]:
                    if isinstance(cond, dict):
                        filter_conditions.append(FilterCondition(**cond))
                    else:
                        filter_conditions.append(cond)
            
            filters = FilterCriteria(
                time_range=data.get("filters", {}).get("time_range"),
                conditions=filter_conditions
            )
            
            return IntentOutput(
                task=data["task"],
                entities=data["entities"],
                attributes=data["attributes"],
                filters=filters,
                systems=data["systems"],
                metric=data.get("metric"),
                aggregation=data.get("aggregation"),
                output_mode=data.get("output_mode", "records"),
                requires_federation=data.get("requires_federation", False),
                priority=data["priority"],
                confidence_score=data["confidence_score"]
            )
            
        except Exception as e:
            raise RuntimeError(f"JSON validation failed:\n{text}\nError: {e}")
    
    def _fallback_extract(self, text: str) -> IntentOutput:
        """
        Rule-based extraction when LLM fails.
        Applies all CRITICAL RULES.
        """
        
        task = self.fallback_extractor.extract_task(text)
        entities = self.fallback_extractor.extract_entities(text)
        attributes = self.fallback_extractor.extract_attributes(text)
        
        # If attributes empty, populate from entity defaults
        if not attributes:
            for entity in entities:
                attributes.extend(DEFAULT_ENTITY_ATTRIBUTES.get(entity, []))
            attributes = list(set(attributes))
        
        # Extract systems (CRITICAL RULE 2)
        systems = self.fallback_extractor.extract_systems(text, entities)

        # Extract metric semantics
        metric = self.fallback_extractor.extract_metric(text)
        aggregation = self.fallback_extractor.extract_aggregation(text)
        output_mode = self.normalizer.infer_output_mode(text, task, aggregation)

        # Extract filters with {field, value} structure (CRITICAL RULE 1)
        filter_list = self.fallback_extractor.extract_filters(text)
        filter_conditions = [FilterCondition(**f) for f in filter_list]
        
        # Extract time range
        time_range = self.normalizer.normalize_date_range(text)
        
        # Priority logic
        if aggregation and task == "fetch":
            task = "analyze"
        priority = infer_priority(task)

        requires_federation = self.normalizer.infer_federation_requirement(
            entities,
            systems,
            metric,
            aggregation,
        )

        if requires_federation:
            for system in ("unisys", "ibm"):
                if system not in systems:
                    systems.append(system)
            if metric == "total_spend" and "transaction" not in entities:
                entities.append("transaction")
                entities = self.normalizer.apply_entity_priority(entities)
                for attr in DEFAULT_ENTITY_ATTRIBUTES.get("transaction", []):
                    if attr not in attributes:
                        attributes.append(attr)

        # Compute confidence
        fallback_data = {
            "task": task,
            "entities": entities,
            "attributes": attributes,
            "filters": {"time_range": time_range, "conditions": filter_list},
            "systems": systems,
            "metric": metric,
            "aggregation": aggregation,
            "output_mode": output_mode,
            "requires_federation": requires_federation,
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
                conditions=filter_conditions
            ),
            systems=systems,
            metric=metric,
            aggregation=aggregation,
            output_mode=output_mode,
            requires_federation=requires_federation,
            priority=priority,
            confidence_score=confidence
        )
