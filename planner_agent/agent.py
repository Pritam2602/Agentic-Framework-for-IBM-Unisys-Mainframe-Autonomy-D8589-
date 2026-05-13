"""LLM-backed Planner Agent.

Architectural role:
  Context Resolution Agent (WHERE) -> Planner Agent (HOW) -> Execution Agent (RUN)

The deterministic planner builds safe execution steps from resolved metadata. The
LLM is optional and may only refine explanation, strategy, and warnings; it must
not invent new systems, credentials, or destructive commands.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from app.agent.execution_planner import ExecutionPlanner
from app.models.schemas import TraceEvent
from app.catalog.catalog_service import CatalogService
from intent_agent.config import build_llm_model

from .schemas import PlannerAgentResponse, PlannerOutput, PlannerStep

logger = logging.getLogger(__name__)


PLANNER_SYSTEM_PROMPT = """
You are an enterprise Planner Agent for a mainframe data federation platform.

Your ONLY job is to explain and refine HOW a grounded intent/context pair should
be executed. You do NOT execute commands, call APIs, modify data, or invent
systems.

You receive:
- Intent Agent output: WHAT the user wants
- Context Resolution Agent output: WHERE the data exists
- Zowe command catalog candidates
- A deterministic grounded plan created from available metadata and catalog commands

Rules:
- Return STRICT JSON only.
- You may refine strategy, reasoning_summary, warnings, and governance_controls.
- You may recommend selected_command_ids, but each ID must exist in the provided
  candidate list.
- You may not add destructive commands.
- You may not add steps that target systems missing from the grounded plan.
- IBM transaction amounts are the financial source of truth.
- Unisys shopping data is behavioral enrichment only.
- When federation is required, preserve customerId as the preferred join key.

Return this JSON shape:
{{
  "strategy": "string",
  "reasoning_summary": "string",
  "selected_command_ids": ["string"],
  "governance_controls": ["string"],
  "warnings": ["string"]
}}
"""


class PlannerAgent:
    """Creates safe execution plans from intent and resolved context."""

    def __init__(self, model: Any = None, enable_llm: bool = True):
        self.model = model if model is not None else (
            build_llm_model(logger=logger) if enable_llm else None
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", PLANNER_SYSTEM_PROMPT), ("user", "{planning_request}")]
        )
        self.catalog_service = CatalogService()
        self.execution_planner = ExecutionPlanner()

    def run(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        use_llm: bool = True,
        mode: str = "safe_mock",
    ) -> PlannerAgentResponse:
        """Build a planner output for the downstream Execution Agent."""
        trace: List[Dict[str, Any]] = []
        warnings: List[str] = []
        self._add_trace(trace, "execution_planning", "Received intent and resolved context")

        plan = self._build_grounded_plan(intent=intent, context=context, mode=mode)
        self._add_trace(
            trace,
            "execution_planning",
            f"Built grounded execution plan with {len(plan.steps)} step(s)",
            plan.model_dump(),
        )

        if use_llm and self.model is not None:
            self._apply_llm_refinement(plan, intent, context, warnings)
        elif use_llm:
            warnings.append("LLM unavailable - used deterministic planning")

        status = "completed" if plan.steps else "partial"
        canonical_output = plan.model_dump()

        return PlannerAgentResponse(
            status=status,
            natural_response=(
                f"Planner created {len(plan.steps)} execution step(s) "
                f"for {plan.objective or 'the resolved request'}."
            ),
            plan=plan,
            canonical_output=canonical_output,
            execution_trace=trace,
            warnings=list(dict.fromkeys([*warnings, *plan.warnings])),
        )

    def _build_grounded_plan(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        mode: str,
    ) -> PlannerOutput:
        params = self._extract_execution_parameters(intent)
        systems = self._resolve_systems(intent, context)
        selected_commands = self._select_commands(intent, context, systems)
        base_plan = self.execution_planner.plan(selected_commands, intent)
        steps: List[PlannerStep] = []
        data_dependencies: List[str] = []

        if "ibm" in systems:
            ibm_context = context.get("ibm") or {}
            dataset = ibm_context.get("dataset") or "CardDemo transactions"
            ibm_command = self._first_command_for_system(selected_commands, "ibm")
            data_dependencies.append(f"ibm:{dataset}")
            steps.append(
                PlannerStep(
                    step_id="fetch-ibm-transactions",
                    order=len(steps) + 1,
                    system="ibm",
                    step_type="ibm_dataset",
                    action="fetch transactions",
                    command=self._render_zowe_command(ibm_command, params, dataset),
                    description=(
                        "Fetch IBM CardDemo transaction records using resolved "
                        "dataset context, extracted filters, and the selected "
                        "Zowe catalog command."
                    ),
                    parameters=params,
                    expected_output="IBM transaction records",
                    risk_level="LOW",
                )
            )

        if "unisys" in systems:
            unisys_context = context.get("unisys") or {}
            endpoint = unisys_context.get("api") or "/api/shopping"
            entity = unisys_context.get("entity") or "shopping"
            data_dependencies.append(f"unisys:{endpoint}")
            depends_on = ["fetch-ibm-transactions"] if "ibm" in systems else []
            steps.append(
                PlannerStep(
                    step_id=f"fetch-unisys-{entity}",
                    order=len(steps) + 1,
                    system="unisys",
                    step_type="unisys_api",
                    action=f"fetch {entity}",
                    endpoint=endpoint,
                    description=(
                        f"Fetch Unisys ePortal {entity} records for the "
                        "resolved request."
                    ),
                    parameters=params,
                    depends_on=depends_on,
                    expected_output=f"Unisys {entity} records",
                    risk_level="LOW",
                )
            )

        federation_required = bool(
            intent.get("requires_federation")
            or context.get("is_federation")
            or len(systems) > 1
        )

        governance_controls = [
            "safe_mock execution mode unless explicitly switched to allowlisted",
            "source lineage must be preserved for every normalized field",
        ]
        if federation_required:
            governance_controls.extend(
                [
                    "customerId is the preferred cross-system join key",
                    "IBM transaction amounts remain the financial authority",
                    "Unisys amounts must not be added to IBM spend totals",
                ]
            )

        objective = self._build_objective(intent)
        strategy = self._build_strategy(systems, federation_required)

        warnings = []
        if not steps:
            warnings.append("No executable systems were resolved from intent/context")

        return PlannerOutput(
            plan_id="planner-agent-plan",
            objective=objective,
            mode=mode if mode in {"safe_mock", "allowlisted"} else "safe_mock",
            strategy=strategy,
            selected_commands=selected_commands,
            execution_sequence=base_plan.get("execution_sequence", []),
            parallel_groups=base_plan.get("parallel_groups", []),
            estimated_duration_seconds=base_plan.get("estimated_duration_seconds", 0),
            rollback_plan=base_plan.get("rollback_plan"),
            steps=steps,
            data_dependencies=data_dependencies,
            federation_required=federation_required,
            join_keys=["customerId"] if federation_required else [],
            normalization_required=True,
            governance_controls=governance_controls,
            stop_on_error=True,
            reasoning_summary=(
                "Plan was grounded in resolved IBM and Unisys context and prepared "
                "for the Execution Agent."
            ),
            warnings=warnings,
        )

    def _apply_llm_refinement(
        self,
        plan: PlannerOutput,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        warnings: List[str],
    ) -> None:
        request = {
            "intent": intent,
            "context": context,
            "zowe_command_candidates": self._compact_commands(plan.selected_commands),
            "grounded_plan": plan.model_dump(),
        }
        try:
            chain = self.prompt | self.model
            result = chain.invoke({"planning_request": json.dumps(request, default=str)})
            json_match = re.search(r"\{[\s\S]*\}", result.content)
            if not json_match:
                raise ValueError("No JSON found in LLM output")
            data = json.loads(json_match.group())

            if isinstance(data.get("strategy"), str) and data["strategy"].strip():
                plan.strategy = data["strategy"].strip()
            if isinstance(data.get("reasoning_summary"), str) and data["reasoning_summary"].strip():
                plan.reasoning_summary = data["reasoning_summary"].strip()
            if isinstance(data.get("selected_command_ids"), list):
                self._apply_command_selection(plan, data["selected_command_ids"])
            if isinstance(data.get("governance_controls"), list):
                plan.governance_controls = list(
                    dict.fromkeys(
                        [
                            *plan.governance_controls,
                            *[str(item) for item in data["governance_controls"]],
                        ]
                    )
                )
            if isinstance(data.get("warnings"), list):
                plan.warnings = list(
                    dict.fromkeys([*plan.warnings, *[str(item) for item in data["warnings"]]])
                )
        except Exception as exc:
            logger.warning("[Planner Agent] LLM refinement failed: %s", exc)
            warnings.append("LLM planning refinement unavailable - used deterministic plan")

    def _select_commands(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any],
        systems: List[str],
    ) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        if "ibm" not in systems:
            return selected

        try:
            catalog = self.catalog_service.get_all_commands()
        except Exception as exc:
            logger.warning("[Planner Agent] Zowe catalog unavailable: %s", exc)
            return selected

        ranked = sorted(
            (self._score_catalog_command(command, intent, context), index, command)
            for index, command in enumerate(catalog)
        )
        ranked.reverse()

        for score, _, command in ranked:
            if score <= 0:
                continue
            selected.append(self._normalize_catalog_command(command, len(selected) + 1))
            if len(selected) >= 2:
                break

        return selected

    def _score_catalog_command(
        self,
        command: Dict[str, Any],
        intent: Dict[str, Any],
        context: Dict[str, Any],
    ) -> int:
        text = " ".join(
            str(command.get(key, "")).lower()
            for key in (
                "id",
                "zowe_command",
                "category",
                "command_family",
                "ibm_artifact",
                "operation",
                "access_pattern",
                "intended_agent",
                "constraints",
            )
        )
        task = str(intent.get("task") or "").lower()
        entities = " ".join(str(item).lower() for item in intent.get("entities", []))
        metric = str(intent.get("metric") or "").lower()
        dataset = str((context.get("ibm") or {}).get("dataset") or "").lower()

        score = 0
        if "zowe files view ds" in text:
            score += 40
        if "zowe files list ds" in text:
            score += 20
        if "dataset" in text or "files" in text:
            score += 15
        if "read" in text:
            score += 10
        if any(token in entities for token in ("transaction", "account", "customer")):
            score += 10
        if "fetch" in task or "total_spend" in metric:
            score += 10
        if dataset and ("dataset" in text or "files" in text):
            score += 5
        if any(word in text for word in ("delete", "upload", "submit", "cancel")):
            score -= 30
        return score

    @staticmethod
    def _normalize_catalog_command(command: Dict[str, Any], index: int) -> Dict[str, Any]:
        zowe_command = command.get("zowe_command") or command.get("command_template") or ""
        command_id = command.get("id") or command.get("command_id") or f"zowe-cmd-{index}"
        return {
            **command,
            "id": command_id,
            "command_id": command_id,
            "name": command.get("name") or str(zowe_command).upper().replace(" ", "_"),
            "system": "ibm",
            "command": zowe_command,
            "zowe_command": zowe_command,
        }

    @staticmethod
    def _first_command_for_system(
        commands: List[Dict[str, Any]],
        system: str,
    ) -> Optional[Dict[str, Any]]:
        for command in commands:
            if command.get("system") == system:
                return command
        return None

    @staticmethod
    def _render_zowe_command(
        command: Optional[Dict[str, Any]],
        params: Dict[str, Any],
        dataset: str,
    ) -> Optional[str]:
        if not command:
            return None

        zowe_command = command.get("zowe_command") or command.get("command")
        if not zowe_command:
            return None

        target_dataset = (
            params.get("primaryIdentifier")
            or params.get("dataset")
            or dataset
            or "USER.DATA"
        )
        rendered = str(zowe_command)
        if "{{primaryIdentifier}}" in rendered:
            rendered = rendered.replace("{{primaryIdentifier}}", str(target_dataset))
        elif "{{qualifier}}" in rendered:
            rendered = rendered.replace("{{qualifier}}", str(target_dataset).split(".")[0])
        elif " ds" in rendered and '"' not in rendered and target_dataset:
            rendered = f'{rendered} "{target_dataset}"'
        return rendered

    def _apply_command_selection(
        self,
        plan: PlannerOutput,
        selected_command_ids: List[Any],
    ) -> None:
        allowed = {
            str(command.get("id") or command.get("command_id")): command
            for command in plan.selected_commands
        }
        ordered = []
        for command_id in selected_command_ids:
            command = allowed.get(str(command_id))
            if command and command not in ordered:
                ordered.append(command)
        if ordered:
            plan.selected_commands = ordered
            allowed_ids = {str(command.get("id") or command.get("command_id")) for command in ordered}
            filtered_sequence = [
                item for item in plan.execution_sequence
                if str(item.get("command_id")) in allowed_ids
            ]
            if filtered_sequence:
                plan.execution_sequence = filtered_sequence

    @staticmethod
    def _compact_commands(commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        compact = []
        for command in commands[:5]:
            compact.append(
                {
                    "id": command.get("id") or command.get("command_id"),
                    "zowe_command": command.get("zowe_command"),
                    "category": command.get("category"),
                    "command_family": command.get("command_family"),
                    "operation": command.get("operation"),
                    "execution_cost": command.get("execution_cost"),
                    "confidence_level": command.get("confidence_level"),
                }
            )
        return compact

    @staticmethod
    def _extract_execution_parameters(intent: Dict[str, Any]) -> Dict[str, Any]:
        filters = intent.get("filters") or {}
        params: Dict[str, Any] = {}
        for condition in filters.get("conditions") or []:
            if isinstance(condition, dict) and condition.get("field"):
                params[str(condition["field"])] = condition.get("value")

        time_range = filters.get("time_range")
        if isinstance(time_range, dict) and "date" not in params:
            params["date"] = time_range.get("start")

        return params

    @staticmethod
    def _resolve_systems(intent: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        systems = [str(system).lower() for system in intent.get("systems", [])]
        if context.get("ibm") and "ibm" not in systems:
            systems.append("ibm")
        if context.get("unisys") and "unisys" not in systems:
            systems.append("unisys")
        return [system for system in systems if system in {"ibm", "unisys"}]

    @staticmethod
    def _build_objective(intent: Dict[str, Any]) -> str:
        task = intent.get("task") or "fetch"
        entities = ", ".join(intent.get("entities") or []) or "records"
        metric = intent.get("metric")
        aggregation = intent.get("aggregation")
        parts = [str(task), str(entities)]
        if metric:
            parts.append(f"metric={metric}")
        if aggregation:
            parts.append(f"aggregation={aggregation}")
        return " | ".join(parts)

    @staticmethod
    def _build_strategy(systems: List[str], federation_required: bool) -> str:
        if federation_required and {"ibm", "unisys"}.issubset(set(systems)):
            return (
                "Fetch IBM financial records first, fetch Unisys behavioral "
                "enrichment second, then normalize both outputs for federation."
            )
        if "ibm" in systems:
            return "Fetch IBM mainframe records through the safe dataset execution path."
        if "unisys" in systems:
            return "Fetch Unisys ePortal records through the safe API execution path."
        return "No executable data source was resolved."

    @staticmethod
    def _add_trace(
        trace: List[Dict[str, Any]],
        stage: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        trace.append(
            TraceEvent(
                timestamp=datetime.now(),
                stage=stage,
                message=message,
                metadata=metadata,
            ).model_dump(mode="json")
        )
