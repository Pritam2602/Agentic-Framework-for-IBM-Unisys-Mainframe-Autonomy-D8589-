"""LLM-backed Execution Agent.

Architectural role:
  Planner Agent (HOW) -> Execution Agent (RUN)

The LLM is used only to normalize and assess a planner JSON. Actual execution is
routed through allowlisted local executors and mock data services.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

from app.execution.dataset_executor import DatasetExecutor
from app.execution.job_executor import JobExecutor
from app.execution.workflow_executor import WorkflowExecutor
from app.mock_zos import MockZOSSimulator
from app.models.schemas import TraceEvent
from intent_agent.config import build_llm_model
from mock_eportal.services.inventory_service import InventoryService
from mock_eportal.services.shopping_service import ShoppingService

from .schemas import (
    ExecutionAgentResponse,
    ExecutionPlan,
    ExecutionStep,
    StepExecutionResult,
)

logger = logging.getLogger(__name__)


EXECUTION_SYSTEM_PROMPT = """
You are an enterprise Execution Agent normalizer for a mainframe federation platform.

Your ONLY job is to convert a Planner Agent JSON into a safe normalized execution plan.
You do NOT invent commands, credentials, hosts, or destructive actions.

Rules:
- Return STRICT JSON only.
- Preserve planner intent, order, parameters, dependencies, and expected outputs.
- Classify each step_type as one of:
  zowe, ibm_job, ibm_dataset, ibm_workflow, unisys_api, noop
- Use system: ibm, unisys, both, or local.
- Mark delete/cancel/upload/start/submit/create/update as MEDIUM or HIGH risk.
- Mark destructive delete/purge/drop as CRITICAL and requires_approval=true.
- If a step is ambiguous, set step_type=noop and explain in description.
- The execution runtime is safe_mock unless the API request explicitly sets allowlisted.

Return this JSON shape:
{{
  "plan_id": "string",
  "objective": "string",
  "mode": "safe_mock",
  "stop_on_error": true,
  "reasoning_summary": "string",
  "steps": [
    {{
      "step_id": "step-1",
      "order": 1,
      "description": "string",
      "system": "ibm|unisys|both|local",
      "step_type": "zowe|ibm_job|ibm_dataset|ibm_workflow|unisys_api|noop",
      "action": "string",
      "command": "string or null",
      "endpoint": "string or null",
      "parameters": {{}},
      "depends_on": [],
      "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
      "requires_approval": false,
      "expected_output": "string or null"
    }}
  ]
}}
"""


class ExecutionAgent:
    """Validates and executes Planner Agent JSON through safe executors."""

    def __init__(self, model: Any = None, enable_llm: bool = True):
        self.model = model if model is not None else (
            build_llm_model(logger=logger) if enable_llm else None
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [("system", EXECUTION_SYSTEM_PROMPT), ("user", "{execution_request}")]
        )
        self.job_executor = JobExecutor()
        self.dataset_executor = DatasetExecutor()
        self.workflow_executor = WorkflowExecutor()
        self.zos_simulator = MockZOSSimulator()
        self.shopping_service = ShoppingService()
        self.inventory_service = InventoryService()

    def run(
        self,
        planner_json: Dict[str, Any],
        intent: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
        mode: str = "safe_mock",
    ) -> ExecutionAgentResponse:
        """Normalize and execute a planner JSON."""
        trace: List[Dict[str, Any]] = []
        warnings: List[str] = []
        self._add_trace(trace, "execution_planning", "Received planner JSON")

        plan = self._normalize_plan(planner_json, intent, context, mode, warnings)
        self._add_trace(
            trace,
            "execution_planning",
            f"Normalized execution plan with {len(plan.steps)} step(s)",
            plan.model_dump(),
        )

        blocked_steps = [step for step in plan.steps if step.requires_approval or step.risk_level == "CRITICAL"]
        if blocked_steps:
            warnings.append(
                "One or more steps require approval and were blocked by the Execution Agent"
            )
            return self._response(
                status="blocked",
                plan=plan,
                results=[],
                trace=trace,
                warnings=warnings,
                dry_run=False,
            )

        if dry_run:
            return self._response(
                status="dry_run",
                plan=plan,
                results=[],
                trace=trace,
                warnings=warnings,
                dry_run=True,
            )

        results: List[StepExecutionResult] = []
        completed_ids: set[str] = set()
        failed = False

        for step in sorted(plan.steps, key=lambda item: item.order):
            missing = [dep for dep in step.depends_on if dep not in completed_ids]
            if missing:
                result = self._skipped_result(step, f"Missing dependencies: {', '.join(missing)}")
                results.append(result)
                failed = True
                if plan.stop_on_error:
                    break
                continue

            result = self._execute_step(step, mode=plan.mode)
            results.append(result)
            self._add_trace(
                trace,
                "execution",
                f"Executed step {step.step_id}: {result.status}",
                result.model_dump(mode="json"),
            )

            if result.status == "completed":
                completed_ids.add(step.step_id)
            else:
                failed = True
                if plan.stop_on_error:
                    break

        status = "completed"
        if failed and any(result.status == "completed" for result in results):
            status = "partial"
        elif failed:
            status = "failed"

        self._add_trace(
            trace,
            "result_collection",
            f"Collected {len(results)} execution result(s)",
            {"status": status},
        )
        return self._response(status, plan, results, trace, warnings, dry_run=False)

    def _normalize_plan(
        self,
        planner_json: Dict[str, Any],
        intent: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
        mode: str,
        warnings: List[str],
    ) -> ExecutionPlan:
        if self.model is not None:
            request = {
                "planner_json": planner_json,
                "intent": intent,
                "context": context,
                "requested_mode": mode,
            }
            try:
                chain = self.prompt | self.model
                result = chain.invoke({"execution_request": json.dumps(request, default=str)})
                plan = self._parse_llm_plan(result.content)
                plan.mode = mode
                return self._post_process_plan(plan)
            except Exception as exc:
                logger.warning("[Execution Agent] LLM normalization failed: %s", exc)
                warnings.append("LLM normalization unavailable - used deterministic planner adapter")

        return self._fallback_normalize(planner_json, mode=mode)

    def _parse_llm_plan(self, text: str) -> ExecutionPlan:
        json_match = re.search(r"\{[\s\S]*\}", text)
        if not json_match:
            raise ValueError("No JSON found in LLM output")
        return ExecutionPlan(**json.loads(json_match.group()))

    def _fallback_normalize(self, planner_json: Dict[str, Any], mode: str) -> ExecutionPlan:
        raw_steps = self._extract_raw_steps(planner_json)
        steps = [
            self._normalize_step(raw_step, index)
            for index, raw_step in enumerate(raw_steps, start=1)
        ]
        if not steps and planner_json:
            steps = [self._normalize_step(planner_json, 1)]

        return self._post_process_plan(
            ExecutionPlan(
                plan_id=str(planner_json.get("plan_id") or planner_json.get("id") or "planner-plan"),
                objective=str(
                    planner_json.get("objective")
                    or planner_json.get("goal")
                    or planner_json.get("summary")
                    or "Execute planner-provided steps"
                ),
                mode=mode,
                steps=steps,
                stop_on_error=bool(planner_json.get("stop_on_error", True)),
                reasoning_summary="Deterministically normalized planner JSON for execution",
            )
        )

    @staticmethod
    def _extract_raw_steps(planner_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        for key in ("steps", "execution_sequence", "commands", "plan"):
            value = planner_json.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _normalize_step(self, raw_step: Dict[str, Any], index: int) -> ExecutionStep:
        command = raw_step.get("command") or raw_step.get("zowe_command") or raw_step.get("command_text")
        action = raw_step.get("action") or raw_step.get("command_name") or raw_step.get("name") or command or "noop"
        endpoint = raw_step.get("endpoint") or raw_step.get("api") or raw_step.get("api_endpoint")
        system = self._infer_system(raw_step, command, endpoint)
        step_type = self._infer_step_type(system, action, command, endpoint)
        parameters = raw_step.get("parameters") or raw_step.get("params") or raw_step.get("input") or {}
        risk = self._infer_risk(action, command)

        return ExecutionStep(
            step_id=str(raw_step.get("step_id") or raw_step.get("id") or f"step-{index}"),
            order=int(raw_step.get("order") or raw_step.get("sequence") or index),
            description=str(raw_step.get("description") or raw_step.get("next_step") or action or ""),
            system=system,
            step_type=step_type,
            action=str(action),
            command=str(command) if command else None,
            endpoint=str(endpoint) if endpoint else None,
            parameters=parameters if isinstance(parameters, dict) else {"value": parameters},
            depends_on=list(raw_step.get("depends_on") or raw_step.get("dependencies") or []),
            risk_level=risk,
            requires_approval=risk == "CRITICAL",
            expected_output=raw_step.get("expected_output"),
        )

    @staticmethod
    def _infer_system(
        raw_step: Dict[str, Any],
        command: Optional[str],
        endpoint: Optional[str],
    ) -> str:
        explicit = str(raw_step.get("system") or raw_step.get("target_system") or "").lower()
        if explicit in {"ibm", "unisys", "both", "local"}:
            return explicit
        text = " ".join(str(part or "").lower() for part in [command, endpoint, raw_step.get("action")])
        if "unisys" in text or "eportal" in text or "/api/shopping" in text or "/api/inventory" in text:
            return "unisys"
        if "zowe" in text or "jcl" in text or "zos" in text or "dataset" in text:
            return "ibm"
        return "local"

    @staticmethod
    def _infer_step_type(
        system: str,
        action: Any,
        command: Optional[str],
        endpoint: Optional[str],
    ) -> str:
        text = " ".join(str(part or "").lower() for part in [action, command, endpoint])
        if system == "unisys" or endpoint:
            return "unisys_api"
        if "transaction" in text:
            return "ibm_dataset"
        if "workflow" in text:
            return "ibm_workflow"
        if "dataset" in text or "listcat" in text or "files" in text or " ds " in f" {text} ":
            return "ibm_dataset"
        if "job" in text or "jcl" in text or "submit" in text:
            return "ibm_job"
        if "zowe" in text:
            return "zowe"
        return "noop"

    @staticmethod
    def _infer_risk(action: Any, command: Optional[str]) -> str:
        text = " ".join(str(part or "").lower() for part in [action, command])
        if any(word in text for word in ["delete", "purge", "drop", "destroy", "uncatalog"]):
            return "CRITICAL"
        if any(word in text for word in ["cancel", "upload", "submit", "create", "start", "stop", "update"]):
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _post_process_plan(plan: ExecutionPlan) -> ExecutionPlan:
        seen: set[str] = set()
        normalized_steps: List[ExecutionStep] = []
        for index, step in enumerate(sorted(plan.steps, key=lambda item: item.order), start=1):
            step.order = index
            if step.step_id in seen:
                step.step_id = f"{step.step_id}-{index}"
            seen.add(step.step_id)
            if step.risk_level == "CRITICAL":
                step.requires_approval = True
            normalized_steps.append(step)
        plan.steps = normalized_steps
        return plan

    def _execute_step(self, step: ExecutionStep, mode: str) -> StepExecutionResult:
        started = datetime.now()
        try:
            command_def = {
                "id": step.step_id,
                "name": step.action.upper().replace(" ", "_"),
                "zowe_command": step.command,
                "category": step.step_type,
            }

            if mode == "safe_mock" and step.command and step.command.strip().lower().startswith("zowe "):
                output = self.zos_simulator.execute(step.command, step.parameters)
            elif step.step_type == "ibm_job":
                output = self.job_executor.execute(command_def, step.parameters)
            elif step.step_type == "ibm_dataset":
                output = self.dataset_executor.execute(command_def, step.parameters)
            elif step.step_type == "ibm_workflow":
                output = self.workflow_executor.execute(command_def, step.parameters)
            elif step.step_type == "zowe":
                output = self._execute_zowe_mock(step)
            elif step.step_type == "unisys_api":
                output = self._execute_unisys_api(step)
            else:
                output = {
                    "status": "completed",
                    "command": step.action,
                    "message": "No operation required for this planner step",
                }

            status = "completed" if output.get("status") not in {"failed", "error"} else "failed"
            return StepExecutionResult(
                step_id=step.step_id,
                order=step.order,
                status=status,
                started_at=started,
                ended_at=datetime.now(),
                system=step.system,
                step_type=step.step_type,
                action=step.action,
                command=step.command,
                output=output,
                error=output.get("error") or output.get("message") if status == "failed" else None,
            )
        except Exception as exc:
            return StepExecutionResult(
                step_id=step.step_id,
                order=step.order,
                status="failed",
                started_at=started,
                ended_at=datetime.now(),
                system=step.system,
                step_type=step.step_type,
                action=step.action,
                command=step.command,
                output={},
                error=str(exc),
            )

    def _execute_zowe_mock(self, step: ExecutionStep) -> Dict[str, Any]:
        return self.zos_simulator.execute(step.command or step.action, step.parameters)

    def _execute_unisys_api(self, step: ExecutionStep) -> Dict[str, Any]:
        params = step.parameters
        endpoint = (step.endpoint or "").lower()
        action = (step.action or "").lower()
        if "inventory" in endpoint or "inventory" in action:
            data = self.inventory_service.search(
                merchant=params.get("merchant"),
                category=params.get("category"),
                sku=params.get("sku"),
                availability_status=params.get("availabilityStatus") or params.get("availability_status"),
            )
            return {
                "status": "completed",
                "source": "unisys",
                "entity": "inventory",
                "endpoint": step.endpoint or "/api/inventory",
                "count": len(data),
                "data": data,
                "note": "Inventory data provides product availability context related to shopping behavior.",
            }

        customer_id = params.get("customerId") or params.get("customer_id")
        date = params.get("date")

        if customer_id is not None and date is not None:
            data = self.shopping_service.get_by_customer_id_and_date(str(customer_id), str(date))
        elif customer_id is not None:
            data = self.shopping_service.get_by_customer_id(str(customer_id))
        elif date is not None:
            data = self.shopping_service.get_by_date(str(date))
        else:
            data = self.shopping_service.get_all()

        return {
            "status": "completed",
            "source": "unisys",
            "entity": "shopping",
            "endpoint": step.endpoint or "/api/shopping",
            "count": len(data),
            "data": data,
            "note": "Unisys data is behavioral enrichment; do not double-count financial amounts with IBM.",
        }

    @staticmethod
    def _skipped_result(step: ExecutionStep, reason: str) -> StepExecutionResult:
        now = datetime.now()
        return StepExecutionResult(
            step_id=step.step_id,
            order=step.order,
            status="skipped",
            started_at=now,
            ended_at=now,
            system=step.system,
            step_type=step.step_type,
            action=step.action,
            command=step.command,
            output={},
            error=reason,
        )

    def _response(
        self,
        status: str,
        plan: ExecutionPlan,
        results: List[StepExecutionResult],
        trace: List[Dict[str, Any]],
        warnings: List[str],
        dry_run: bool,
    ) -> ExecutionAgentResponse:
        successful = sum(1 for result in results if result.status == "completed")
        canonical_output = {
            "plan_id": plan.plan_id,
            "objective": plan.objective,
            "total_steps": len(plan.steps),
            "executed_steps": len(results),
            "successful_steps": successful,
            "failed_steps": sum(1 for result in results if result.status == "failed"),
            "results": [result.model_dump(mode="json") for result in results],
        }

        if dry_run:
            natural = f"Plan validated. {len(plan.steps)} step(s) are ready for execution."
        elif status == "blocked":
            natural = "Execution blocked because at least one planner step requires approval."
        else:
            natural = f"Execution {status}. {successful}/{len(results)} executed step(s) completed successfully."

        return ExecutionAgentResponse(
            status=status,
            natural_response=natural,
            normalized_plan=plan,
            step_results=results,
            canonical_output=canonical_output,
            execution_trace=trace,
            warnings=warnings,
        )

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
