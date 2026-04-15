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

import json
import logging
import re
from typing import Dict, Any, Optional, Union, List

from langchain_core.prompts import ChatPromptTemplate

from .schemas import ContextOutput, IBMContext, UnisysContext
from .ibm_resolver import IBMContextResolver
from .unisys_resolver import UnisysContextResolver

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

    def __init__(self, model=None, eportal_url: str = None):
        self.ibm_resolver = IBMContextResolver()
        self.unisys_resolver = UnisysContextResolver(base_url=eportal_url)
        self.model = model
        self._init_llm()

    def _init_llm(self):
        """Initialize the LLM model if not provided"""
        if self.model is None:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.model = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0
                )
                logger.info("[Context Agent] Gemini LLM initialized")
            except Exception as e:
                logger.warning(f"[Context Agent] LLM init failed: {e}")
                self.model = None

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
        unisys_metadata = self._gather_unisys_metadata(entities) if "unisys" in systems else None

        # Use LLM to reason about the best resolution
        if self.model:
            return self._llm_resolve(
                intent_data, ibm_metadata, unisys_metadata, systems
            )
        else:
            # Fallback to rule-based resolution
            logger.warning("[Context Agent] LLM unavailable, using rule-based fallback")
            return self._fallback_resolve(
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
        metadata = {"tools": [], "schemas": []}

        for entity in entities:
            tool = self.unisys_resolver._discover_tool(entity)
            if tool:
                metadata["tools"].append(tool)

            schema = self.unisys_resolver._get_schema(entity)
            if schema:
                metadata["schemas"].append(schema)

        return metadata

    def _llm_resolve(
        self,
        intent_data: Dict[str, Any],
        ibm_metadata: Optional[Dict[str, Any]],
        unisys_metadata: Optional[Dict[str, Any]],
        systems: List[str],
    ) -> ContextOutput:
        """Use LLM to reason about the best resolution"""

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
        }

        request_text = json.dumps(request, indent=2, default=str)

        try:
            chain = self.prompt | self.model
            result = chain.invoke({"resolution_request": request_text})
            return self._parse_llm_response(result.content, systems, intent_data)
        except Exception as e:
            logger.error(f"[Context Agent] LLM resolution failed: {e}")
            return self._fallback_resolve(
                intent_data, ibm_metadata, unisys_metadata, systems
            )

    def _parse_llm_response(
        self, text: str, systems: List[str], intent_data: Dict[str, Any]
    ) -> ContextOutput:
        """Parse LLM response JSON into ContextOutput"""
        try:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                raise ValueError("No JSON found in LLM output")

            data = json.loads(json_match.group())

            # Build IBM context
            ibm_context = None
            if "ibm" in systems and data.get("ibm"):
                ibm_data = data["ibm"]
                ibm_context = IBMContext(
                    program=ibm_data.get("program"),
                    program_name=ibm_data.get("program_description", ""),
                    dataset=ibm_data.get("primary_dataset"),
                    all_datasets=ibm_data.get("all_datasets", []),
                    jcl_job=ibm_data.get("jcl_job"),
                    jcl_steps=[],
                    zowe_commands=[],
                    variables=[
                        {"name": v, "level": 5, "pic": "", "usage": ""}
                        for v in ibm_data.get("key_variables", [])
                    ],
                    io_operations={},
                )

            # Build Unisys context
            unisys_context = None
            if "unisys" in systems and data.get("unisys"):
                u_data = data["unisys"]
                unisys_context = UnisysContext(
                    api=u_data.get("api_endpoint"),
                    fields=u_data.get("fields", []),
                    tool_name=u_data.get("tool_name"),
                    params=[
                        {"name": p, "type": "string", "required": False}
                        for p in u_data.get("params", [])
                    ],
                    schema_endpoint=f"/schema/{intent_data.get('entities', [''])[0]}",
                    entity=intent_data.get("entities", [None])[0],
                )

            confidence = data.get("resolution_confidence", 0.7)
            reasoning = data.get("reasoning_summary", "")

            resolved_entities = []
            if ibm_context and ibm_context.program:
                resolved_entities.append(
                    f"ibm:{intent_data.get('entities', [''])[0]}"
                )
            if unisys_context and unisys_context.api:
                resolved_entities.append(
                    f"unisys:{intent_data.get('entities', [''])[0]}"
                )

            return ContextOutput(
                ibm=ibm_context,
                unisys=unisys_context,
                entities_resolved=resolved_entities,
                systems_checked=systems,
                resolution_confidence=min(max(confidence, 0.0), 1.0),
                warnings=[reasoning] if reasoning else [],
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
    ) -> ContextOutput:
        """Rule-based fallback when LLM is unavailable"""
        entities = intent_data.get("entities", [])
        attributes = intent_data.get("attributes", [])

        ibm_context = None
        unisys_context = None
        resolved = []
        warnings = ["LLM unavailable — used rule-based fallback resolution"]

        if "ibm" in systems:
            for entity in entities:
                ctx = self.ibm_resolver.resolve(entity, attributes)
                if ctx:
                    ibm_context = ctx
                    resolved.append(f"ibm:{entity}")
                    break

        if "unisys" in systems:
            for entity in entities:
                ctx = self.unisys_resolver.resolve(entity, attributes)
                if ctx:
                    unisys_context = ctx
                    resolved.append(f"unisys:{entity}")
                    break

        confidence = self._compute_confidence(ibm_context, unisys_context, systems)

        return ContextOutput(
            ibm=ibm_context,
            unisys=unisys_context,
            entities_resolved=resolved,
            systems_checked=systems,
            resolution_confidence=confidence,
            warnings=warnings,
        )

    @staticmethod
    def _compute_confidence(
        ibm_ctx: Optional[IBMContext],
        unisys_ctx: Optional[UnisysContext],
        systems: List[str],
    ) -> float:
        """Compute confidence for fallback resolution"""
        score = 0.3
        requested = len(systems)
        resolved = 0

        if "ibm" in systems and ibm_ctx:
            resolved += 1
            if ibm_ctx.program:
                score += 0.15
            if ibm_ctx.jcl_job:
                score += 0.1
            if ibm_ctx.dataset:
                score += 0.1

        if "unisys" in systems and unisys_ctx:
            resolved += 1
            if unisys_ctx.api:
                score += 0.15
            if unisys_ctx.fields:
                score += 0.1

        if requested > 0 and resolved == requested:
            score += 0.1

        return min(max(score, 0.0), 1.0)
