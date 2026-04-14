"""
Pydantic models for API request/response validation
"""
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel


class TraceEvent(BaseModel):
    """Single event in agent execution trace"""
    timestamp: datetime
    stage: Literal["intent_parsing", "capability_matching", "command_selection", 
                   "execution_planning", "execution", "result_collection"]
    message: str
    metadata: Optional[Dict[str, Any]] = None


class CanonicalOutput(BaseModel):
    """Structured output from command execution"""
    type: Literal["json", "table", "file", "text"]
    data: Any
    fileReference: Optional[str] = None


class AgentResponse(BaseModel):
    """Strict agent response model"""
    natural_response: str
    canonical_output: CanonicalOutput
    execution_trace: List[TraceEvent]


class AgentQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class CommandModel(BaseModel):
    id: str
    zowe_command: str
    category: str
    command_family: str
    subsystem: str
    ibm_artifact: str
    operation: str
    access_pattern: Optional[str] = None
    response_format: Optional[str] = None
    intended_agent: Optional[str] = None
    constraints: Optional[str] = None
    execution_cost: str
    confidence_level: Optional[float] = None


class JobModel(BaseModel):
    id: str
    name: str
    scope: Literal["user", "system", "enterprise"]
    mainframe: str
    type: Literal["JCL", "COBOL", "PROC", "DATASET", "WORKFLOW"]
    accessLevel: Literal["read-only", "admin", "restricted"]
    status: Literal["active", "inactive", "pending"]
    lastRun: Optional[datetime] = None
    downloadUrl: Optional[str] = None


class WorkflowModel(BaseModel):
    id: str
    name: str
    scope: Literal["user", "system", "enterprise"]
    mainframe: str
    type: Literal["JCL", "COBOL", "PROC", "DATASET", "WORKFLOW"]
    accessLevel: Literal["read-only", "admin", "restricted"]
    status: Literal["active", "inactive", "pending"]
    lastRun: Optional[datetime] = None
    steps: int
    dependencies: List[str]
    downloadUrl: Optional[str] = None


class DatasetModel(BaseModel):
    id: str
    name: str
    scope: Literal["user", "system", "enterprise"]
    mainframe: str
    type: Literal["JCL", "COBOL", "PROC", "DATASET", "WORKFLOW"]
    accessLevel: Literal["read-only", "admin", "restricted"]
    size: str
    records: int
    downloadUrl: Optional[str] = None


class CatalogStatsModel(BaseModel):
    totalCommands: int
    totalJobs: int
    totalWorkflows: int
    totalDatasets: int
    lastUpdated: datetime


class AgentStatusModel(BaseModel):
    id: str
    name: str
    status: Literal["online", "idle", "busy", "offline"]
    capabilities: List[str]
    uptime: int
    tasksCompleted: int
    lastActivity: datetime


class AgentExecutionModel(BaseModel):
    id: str
    taskId: str
    command: str
    status: Literal["pending", "running", "completed", "failed"]
    startTime: datetime
    endTime: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


class AgentConfigModel(BaseModel):
    environment: str
    version: str
    maxConcurrentTasks: int
    timeout: int
    retryPolicy: Dict[str, int]


class LoanApplicationRequest(BaseModel):
    applicant_id: str
    name: str
    age: int
    income: float
    credit_score: int
    loan_amount: float
    loan_term_months: int
    purpose: str


class LoanEligibilityResult(BaseModel):
    eligible: bool
    reason: Optional[str] = None
    max_loan_amount: float
    recommended_term: int


class LoanInterestResult(BaseModel):
    base_rate: float
    risk_adjustment: float
    final_rate: float
    monthly_payment: float
    total_interest: float


class LoanApprovalResult(BaseModel):
    approved: bool
    loan_id: Optional[str] = None
    approval_amount: float
    interest_rate: float
    monthly_payment: float
    reason: Optional[str] = None


class LoanProcessingResponse(BaseModel):
    application_id: str
    status: str
    eligibility: LoanEligibilityResult
    interest_calculation: Optional[LoanInterestResult] = None
    approval: Optional[LoanApprovalResult] = None
    execution_trace: List[TraceEvent]
