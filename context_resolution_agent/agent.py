"""
agent.py - LLM-Powered Context Resolution Agent

Uses Google Gemini to intelligently resolve WHERE data exists across
IBM and Unisys systems. The LLM reasons over:
  - ProLeap COBOL parsed metadata (programs, variables, I/O)
  - JCL parsed metadata (jobs, steps, datasets)
  - Unisys MCP tool manifests
  - Unisys schema definitions

ARCHITECTURAL ROLE:
  Intent Agent (WHAT) → Context Resolution Agent (WHERE) → Planner Agent (HOW)

MUST NOT:
  ❌ Execute commands
  ❌ Call data APIs
  ❌ Modify any data
  ❌ Submit jobs

MUST ONLY:
  ✅ Resolve metadata using LLM reasoning
  ✅ Discover capabilities
  ✅ Map entities to data sources
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional, Union, List

from langchain_core.prompts import ChatPromptTemplate

from .schemas import ContextOutput, IBMContext, UnisysContext
from .ibm_resolver import IBMContextResolver
from .unisys_resolver import UnisysContextResolver
from intent_agent.config import build_llm_model

logger = logging.getLogger(__name__)


# ================================================================
# LLM SYSTEM PROMPT
# ================================================================

CONTEXT_RESOLUTION_SYSTEM_PROMPT = """
You are an enterprise Context Resolution Agent for a data federation platform.

Your ONLY job is to determine WHERE data exists across IBM Mainframe and Unisys systems.

You are given:
1. A structured intent (what the user wants)
2. IBM metadata (COBOL programs, JCL jobs, datasets from the CardDemo application)
3. Unisys metadata (ePortal APIs, schemas, MCP tools)

You MUST return a JSON object that maps the user's entities to their data locations.

You do NOT:
- Execute commands
- Call APIs
- Plan execution (that's the Planner Agent's job)
- Modify data

For IBM, identify:
- The best matching COBOL program for the entity
- The JCL job that runs that program
- The primary dataset(s) involved
- Key variables from the COBOL program

For Unisys, identify:
- The REST API endpoint
- Available fields
- The MCP tool name
- Supported query parameters

Federation rule:
- If the user asks for shopping or shopping_data, resolve Unisys to the shopping
  behavior API and resolve IBM to transaction context. Shopping maps to IBM
  transactions through customerId, comparable date fields, and comparable
  numeric amount fields.

Return STRICT JSON with this structure:
{{
  "ibm": {{
    "program": "PROGRAM_ID",
    "program_description": "what this program does",
    "jcl_job": "JOB_NAME or null",
    "primary_dataset": "DATASET.NAME or null",
    "all_datasets": ["DS1", "DS2"],
    "key_variables": ["VAR1", "VAR2"],
    "reasoning": "why this program was selected"
  }},
  "unisys": {{
    "api_endpoint": "/api/unisys/entity",
    "fields": ["field1", "field2"],
    "tool_name": "get_entity",
    "params": ["param1", "param2"],
    "reasoning": "why this API was selected"
  }},
  "resolution_confidence": 0.0,
  "reasoning_summary": "overall explanation"
}}

If a system is not in the requested systems list, set its section to null.
Be precise and only select programs/APIs that genuinely match the entity.
"""


class ContextResolutionAgent:
    """
    LLM-Powered Context Resolution Agent

    Uses Google Gemini to intelligently reason about where data exists
    across IBM mainframe and Unisys systems, based on parsed COBOL/JCL
    metadata and Unisys MCP tool manifests.
    """

    def __init__(self, model=None, eportal_url: str = None, enable_llm: bool = True):
        self.ibm_resolver = IBMContextResolver()
        self.unisys_resolver = UnisysContextResolver(base_url=eportal_url)
        self.model = model
        self._init_llm(enable_llm=enable_llm)

    def _init_llm(self, enable_llm: bool = True):
        """Initialize the LLM model if not provided"""
        if not enable_llm:
            self.model = None
        elif self.model is None:
            self.model = build_llm_model(logger=logger)
            if self.model is not None:
                candidates = getattr(self.model, "model_candidates", [])
                logger.info(
                    f"[Context Agent] Gemini LLM initialized with fallback chain={candidates}"
                )
            else:
                logger.warning("[Context Agent] LLM init failed for all configured Gemini models")

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", CONTEXT_RESOLUTION_SYSTEM_PROMPT),
            ("user", "{resolution_request}")
        ])

    def resolve(self, intent: Union[Dict[str, Any], Any]) -> ContextOutput:
        """
        Resolve data context from intent JSON using LLM reasoning.

        Args:
            intent: Intent output (dict or Pydantic model)

        Returns:
            ContextOutput with resolved IBM and Unisys context
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.resolve_async(intent))
        raise RuntimeError(
            "ContextResolutionAgent.resolve() cannot be used inside a running event "
            "loop. Use 'await resolve_async(...)' instead."
        )

    async def resolve_async(self, intent: Union[Dict[str, Any], Any]) -> ContextOutput:
        """
        Resolve data context from intent JSON using LLM reasoning from async code.

        Args:
            intent: Intent output (dict or Pydantic model)

        Returns:
            ContextOutput with resolved IBM and Unisys context
        """
        # Handle both dict and Pydantic model input
        if hasattr(intent, "model_dump"):
            intent_data = intent.model_dump()
        elif isinstance(intent, dict):
            intent_data = intent
        else:
            raise ValueError(f"Invalid intent type: {type(intent)}")

        entities = intent_data.get("entities", [])
        systems = intent_data.get("systems", [])
        attributes = intent_data.get("attributes", [])
        task = intent_data.get("task", "fetch")

        logger.info(
            f"[Context Agent] Resolving: entities={entities}, "
            f"systems={systems}, task={task}"
        )

        # Gather metadata from both systems
        ibm_metadata = self._gather_ibm_metadata(entities) if "ibm" in systems else None
        unisys_metadata = (
            await self._gather_unisys_metadata_async(entities)
            if "unisys" in systems
            else None
        )

        # Use LLM to reason about the best resolution
        if self.model:
            return await self._llm_resolve_async(
                intent_data, ibm_metadata, unisys_metadata, systems
            )
        else:
            # Fallback to rule-based resolution
            logger.warning("[Context Agent] LLM unavailable, using rule-based fallback")
            return await self._fallback_resolve_async(
                intent_data, ibm_metadata, unisys_metadata, systems
            )

    def _gather_ibm_metadata(self, entities: List[str]) -> Dict[str, Any]:
        """Gather IBM metadata for the LLM to reason over"""
        metadata = {"programs": [], "jobs": []}

        for entity in entities:
            programs = self.ibm_resolver._find_programs_for_entity(entity)
            for prog in programs[:3]:  # Top 3 matches
                # Compact representation for LLM
                metadata["programs"].append({
                    "program_id": prog.get("program_id"),
                    "source_file": prog.get("source_file"),
                    "description": prog.get("description", ""),
                    "copybooks": prog.get("copybooks", []),
                    "calls": prog.get("calls", []),
                    "files": prog.get("files", []),
                    "io_operations": prog.get("io_operations", {}),
                    "summary": prog.get("summary", {}),
                    "key_variables": [
                        v["name"] for v in prog.get("variables", [])[:15]
                        if v.get("name") and v.get("pic")
                    ],
                })

            # Find related JCL jobs
            for prog in programs[:3]:
                pid = prog.get("program_id", "")
                jobs = self.ibm_resolver._find_jobs_for_program(pid)
                for job in jobs[:2]:
                    metadata["jobs"].append({
                        "job_name": job.get("job_name"),
                        "steps": job.get("steps", []),
                    })

        return metadata

    def _gather_unisys_metadata(self, entities: List[str]) -> Dict[str, Any]:
        """Gather Unisys metadata for the LLM to reason over"""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._gather_unisys_metadata_async(entities))
        raise RuntimeError(
            "ContextResolutionAgent._gather_unisys_metadata() cannot be used inside "
            "a running event loop. Use 'await _gather_unisys_metadata_async(...)' instead."
        )

    async def _gather_unisys_metadata_async(self, entities: List[str]) -> Dict[str, Any]:
        """Gather Unisys metadata for the LLM to reason over."""
        metadata = {"tools": [], "schemas": []}

        for entity in entities:
            ctx = await self.unisys_resolver.resolve_async(entity)
            if ctx:
                metadata["tools"].append({
                    "tool_name": ctx.tool_name,
                    "api": ctx.api,
                    "entity": ctx.entity,
                    "params": ctx.params,
                    "fields": ctx.fields,
                })
                if ctx.schema_endpoint:
                    metadata["schemas"].append({
                        "entity": ctx.entity,
                        "schema_uri": ctx.schema_endpoint,
                        "fields": ctx.fields,
                    })

        return metadata

    def _llm_resolve(
        self,
        intent_data: Dict[str, Any],
        ibm_metadata: Optional[Dict[str, Any]],
        unisys_metadata: Optional[Dict[str, Any]],
        systems: List[str],
    ) -> ContextOutput:
        """Use LLM to explain a grounded resolution without replacing it."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self._llm_resolve_async(
                    intent_data, ibm_metadata, unisys_metadata, systems
                )
            )
        raise RuntimeError(
            "ContextResolutionAgent._llm_resolve() cannot be used inside a running "
            "event loop. Use 'await _llm_resolve_async(...)' instead."
        )

    async def _llm_resolve_async(
        self,
        intent_data: Dict[str, Any],
        ibm_metadata: Optional[Dict[str, Any]],
        unisys_metadata: Optional[Dict[str, Any]],
        systems: List[str],
    ) -> ContextOutput:
        """Use LLM to explain a grounded resolution without replacing it."""

        grounded = await self._fallback_resolve_async(
            intent_data,
            ibm_metadata,
            unisys_metadata,
            systems,
            include_warning=False,
        )

        # Build the resolution request for the LLM
        request = {
            "intent": {
                "task": intent_data.get("task"),
                "entities": intent_data.get("entities"),
                "attributes": intent_data.get("attributes"),
                "systems": systems,
            },
            "ibm_metadata": ibm_metadata,
            "unisys_metadata": unisys_metadata,
            "grounded_resolution": grounded.model_dump(),
        }

        request_text = json.dumps(request, indent=2, default=str)

        try:
            chain = self.prompt | self.model
            result = chain.invoke({"resolution_request": request_text})
            return self._parse_llm_response(
                result.content,
                systems,
                intent_data,
                grounded,
            )
        except Exception as e:
            logger.error(f"[Context Agent] LLM resolution failed: {e}")
            grounded.warnings.append("LLM unavailable — used grounded resolver output")
            return grounded

    def _parse_llm_response(
        self,
        text: str,
        systems: List[str],
        intent_data: Dict[str, Any],
        grounded: ContextOutput,
    ) -> ContextOutput:
        """Parse LLM response JSON and merge only explanatory fields."""
        try:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                raise ValueError("No JSON found in LLM output")

            data = json.loads(json_match.group())

            confidence = data.get("resolution_confidence", 0.7)
            reasoning = data.get("reasoning_summary", "")

            warnings = []
            if reasoning:
                warnings.append(reasoning)
            warnings.extend(grounded.warnings)
            warnings = list(dict.fromkeys(warnings))

            return ContextOutput(
                ibm=grounded.ibm,
                unisys=grounded.unisys,
                entity_mapping=grounded.entity_mapping,
                entities_resolved=grounded.entities_resolved,
                systems_checked=systems,
                resolution_confidence=max(
                    round(min(max(confidence, 0.0), 0.92), 2),
                    grounded.resolution_confidence,
                ),
                is_federation=grounded.is_federation,
                reasoning_summary=reasoning or grounded.reasoning_summary,
                warnings=grounded.warnings,
            )

        except Exception as e:
            logger.error(f"[Context Agent] Failed to parse LLM response: {e}")
            raise

    def _fallback_resolve(
        self,
        intent_data: Dict[str, Any],
        ibm_metadata: Optional[Dict[str, Any]],
        unisys_metadata: Optional[Dict[str, Any]],
        systems: List[str],
        include_warning: bool = True,
    ) -> ContextOutput:
        """Rule-based fallback when LLM is unavailable"""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self._fallback_resolve_async(
                    intent_data,
                    ibm_metadata,
                    unisys_metadata,
                    systems,
                    include_warning=include_warning,
                )
            )
        raise RuntimeError(
            "ContextResolutionAgent._fallback_resolve() cannot be used inside a "
            "running event loop. Use 'await _fallback_resolve_async(...)' instead."
        )

    async def _fallback_resolve_async(
        self,
        intent_data: Dict[str, Any],
        ibm_metadata: Optional[Dict[str, Any]],
        unisys_metadata: Optional[Dict[str, Any]],
        systems: List[str],
        include_warning: bool = True,
    ) -> ContextOutput:
        """Rule-based fallback when LLM is unavailable."""
        entities = intent_data.get("entities", [])
        attributes = intent_data.get("attributes", [])

        ibm_context = None
        unisys_context = None
        entity_mapping = {}
        resolved = []
        warnings = ["LLM unavailable — used rule-based fallback resolution"] if include_warning else []

        if "ibm" in systems:
            for entity in entities:
                ctx = self.ibm_resolver.resolve(entity, attributes)
                if ctx:
                    ibm_context = ctx
                    resolved.append(f"ibm:{self._resolved_entity_label('ibm', entity)}")
                    break

        if "unisys" in systems:
            for entity in entities:
                ctx = await self.unisys_resolver.resolve_async(entity, attributes)
                if ctx:
                    unisys_context = ctx
                    resolved.append(f"unisys:{self._resolved_entity_label('unisys', entity)}")
                    break

        is_federation = bool(ibm_context and unisys_context and len(systems) > 1)
        if is_federation:
            entity_mapping = self._build_entity_mapping(intent_data)

        confidence = self._compute_confidence(ibm_context, unisys_context, systems)

        return ContextOutput(
            ibm=ibm_context,
            unisys=unisys_context,
            entity_mapping=entity_mapping,
            entities_resolved=resolved,
            systems_checked=systems,
            resolution_confidence=confidence,
            is_federation=is_federation,
            reasoning_summary=self._build_reasoning_summary(ibm_context, unisys_context, is_federation),
            warnings=warnings,
        )

    @staticmethod
    def _compute_confidence(
        ibm_ctx: Optional[IBMContext],
        unisys_ctx: Optional[UnisysContext],
        systems: List[str],
    ) -> float:
        """Compute confidence for fallback resolution"""
        score = 0.35
        requested = len(systems)
        resolved = 0

        if "ibm" in systems and ibm_ctx:
            resolved += 1
            if ibm_ctx.program:
                score += 0.12
            if ibm_ctx.jcl_job:
                score += 0.08
            if ibm_ctx.dataset:
                score += 0.08

        if "unisys" in systems and unisys_ctx:
            resolved += 1
            if unisys_ctx.api:
                score += 0.12
            if unisys_ctx.fields:
                score += 0.07

        if requested > 0 and resolved == requested:
            score += 0.1

        return round(min(max(score, 0.0), 0.92), 2)

    @staticmethod
    def _resolved_entity_label(system: str, entity: str) -> str:
        entity_lower = entity.lower()
        if system == "ibm" and entity_lower in {"shopping", "shopping_data", "transaction"}:
            return "transactions"
        return entity_lower

    @staticmethod
    def _build_entity_mapping(intent_data: Dict[str, Any]) -> Dict[str, str]:
        mapping = {"customerId": "customerId", "date": "transactionDate"}
        mapping["amount"] = "transactionAmount" if intent_data.get("metric") == "total_spend" else "amount"
        return mapping

    @staticmethod
    def _build_reasoning_summary(
        ibm_ctx: Optional[IBMContext],
        unisys_ctx: Optional[UnisysContext],
        is_federation: bool,
    ) -> Optional[str]:
        if is_federation and ibm_ctx and unisys_ctx:
            return (
                "Total spend requires combining IBM transaction data with "
                "Unisys shopping data using customerId as join key and date alignment"
            )
        if ibm_ctx and ibm_ctx.dataset:
            return f"IBM data lives in {ibm_ctx.dataset}"
        if unisys_ctx and unisys_ctx.api:
            return f"Unisys data lives behind {unisys_ctx.api}"
        return None
