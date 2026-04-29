"""Pydantic schemas for the LLM-backed Execution Agent."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


StepType = Literal["zowe", "ibm_job", "ibm_dataset", "ibm_workflow", "unisys_api", "noop"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
StepStatus = Literal["pending", "running", "completed", "failed", "skipped", "blocked"]


class ExecutionStep(BaseModel):
    """Single normalized execution step from a Planner Agent JSON."""

    step_id: str = Field(description="Stable unique ID within this plan")
    order: int = Field(ge=1, description="1-based execution order")
    description: str = Field(default="", description="Human-readable step purpose")
    system: Literal["ibm", "unisys", "both", "local"] = Field(default="local")
    step_type: StepType = Field(default="noop")
    action: str = Field(default="", description="Action or command family to execute")
    command: Optional[str] = Field(default=None, description="Planner-provided command text")
    endpoint: Optional[str] = Field(default=None, description="Unisys/ePortal endpoint when applicable")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = Field(default="LOW")
    requires_approval: bool = Field(default=False)
    expected_output: Optional[str] = None

    @field_validator("step_id")
    @classmethod
    def validate_step_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("step_id cannot be empty")
        return value


class ExecutionPlan(BaseModel):
    """Normalized execution plan consumed by the Execution Agent."""

    plan_id: str = Field(default="planner-plan")
    objective: str = Field(default="")
    mode: Literal["safe_mock", "allowlisted"] = Field(default="safe_mock")
    steps: List[ExecutionStep] = Field(default_factory=list)
    stop_on_error: bool = Field(default=True)
    reasoning_summary: Optional[str] = None


class StepExecutionResult(BaseModel):
    """Result of one execution step."""

    step_id: str
    order: int
    status: StepStatus
    started_at: datetime
    ended_at: datetime
    system: str
    step_type: str
    action: str
    command: Optional[str] = None
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ExecutionAgentRequest(BaseModel):
    """API request for executing a Planner Agent output."""

    planner_json: Dict[str, Any] = Field(description="Planner Agent JSON output")
    intent: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    dry_run: bool = Field(default=False, description="Validate and normalize without executing steps")
    mode: Literal["safe_mock", "allowlisted"] = Field(default="safe_mock")


class ExecutionAgentResponse(BaseModel):
    """Execution Agent response returned to clients."""

    status: Literal["completed", "failed", "partial", "dry_run", "blocked"]
    natural_response: str
    normalized_plan: ExecutionPlan
    step_results: List[StepExecutionResult] = Field(default_factory=list)
    canonical_output: Dict[str, Any] = Field(default_factory=dict)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
