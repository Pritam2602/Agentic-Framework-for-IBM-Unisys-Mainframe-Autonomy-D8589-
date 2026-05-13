"""Pydantic schemas for the Planner Agent."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


PlanMode = Literal["safe_mock", "allowlisted"]
PlannedSystem = Literal["ibm", "unisys", "both", "local"]
PlannedStepType = Literal["ibm_dataset", "ibm_job", "ibm_workflow", "unisys_api", "zowe", "noop"]
RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class PlannerStep(BaseModel):
    """Single Planner Agent step consumed downstream by the Execution Agent."""

    step_id: str = Field(description="Stable unique ID within the plan")
    order: int = Field(ge=1, description="1-based execution order")
    system: PlannedSystem = Field(description="Target system for this step")
    step_type: PlannedStepType = Field(default="noop")
    action: str = Field(description="Execution action to perform")
    description: str = Field(default="")
    command: Optional[str] = Field(default=None)
    endpoint: Optional[str] = Field(default=None)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    expected_output: Optional[str] = None
    risk_level: RiskLevel = Field(default="LOW")
    requires_approval: bool = Field(default=False)

    @field_validator("step_id")
    @classmethod
    def validate_step_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("step_id cannot be empty")
        return value


class PlannerOutput(BaseModel):
    """Execution plan produced by the Planning Layer."""

    plan_id: str = Field(default="planner-plan")
    objective: str = Field(default="")
    mode: PlanMode = Field(default="safe_mock")
    strategy: str = Field(default="")
    selected_commands: List[Dict[str, Any]] = Field(default_factory=list)
    execution_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    parallel_groups: List[List[int]] = Field(default_factory=list)
    estimated_duration_seconds: int = Field(default=0)
    rollback_plan: Optional[Dict[str, Any]] = None
    steps: List[PlannerStep] = Field(default_factory=list)
    data_dependencies: List[str] = Field(default_factory=list)
    federation_required: bool = Field(default=False)
    join_keys: List[str] = Field(default_factory=list)
    normalization_required: bool = Field(default=True)
    governance_controls: List[str] = Field(default_factory=list)
    stop_on_error: bool = Field(default=True)
    reasoning_summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class PlannerAgentRequest(BaseModel):
    """API request for the Planner Agent."""

    intent: Dict[str, Any] = Field(description="Intent Agent output")
    context: Dict[str, Any] = Field(description="Context Resolution Agent output")
    use_llm: bool = Field(default=True)
    mode: PlanMode = Field(default="safe_mock")


class PlannerAgentResponse(BaseModel):
    """Planner Agent response."""

    status: Literal["completed", "partial", "failed"]
    natural_response: str
    plan: PlannerOutput
    canonical_output: Dict[str, Any] = Field(default_factory=dict)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
