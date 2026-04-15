"""
schemas.py - Pydantic models for Context Resolution Agent output
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class IBMContext(BaseModel):
    """Resolved context for IBM mainframe side"""
    program: Optional[str] = Field(None, description="Primary COBOL program ID")
    program_name: Optional[str] = Field(None, description="Human-readable program name")
    dataset: Optional[str] = Field(None, description="Primary dataset name")
    all_datasets: List[str] = Field(default_factory=list, description="All related datasets")
    jcl_job: Optional[str] = Field(None, description="JCL job that executes the program")
    jcl_steps: List[Dict[str, Any]] = Field(default_factory=list, description="JCL step metadata")
    zowe_commands: List[Dict[str, Any]] = Field(default_factory=list, description="Available Zowe commands")
    variables: List[Dict[str, Any]] = Field(default_factory=list, description="COBOL variable definitions")
    io_operations: Dict[str, List[str]] = Field(default_factory=dict, description="File I/O operations")


class UnisysContext(BaseModel):
    """Resolved context for Unisys ePortal side"""
    api: Optional[str] = Field(None, description="REST API endpoint")
    fields: List[str] = Field(default_factory=list, description="Available data fields")
    tool_name: Optional[str] = Field(None, description="MCP tool name")
    params: List[Dict[str, Any]] = Field(default_factory=list, description="Supported query parameters")
    schema_endpoint: Optional[str] = Field(None, description="Schema discovery endpoint")
    entity: Optional[str] = Field(None, description="Entity name")


class ContextOutput(BaseModel):
    """
    Complete Context Resolution Output.

    This is the output of the Context Resolution Agent.
    It tells the Planner Agent WHERE data exists across both systems.

    DOES NOT: execute commands, call APIs, or modify data.
    ONLY: resolves metadata about data locations and capabilities.
    """
    ibm: Optional[IBMContext] = Field(None, description="IBM mainframe context")
    unisys: Optional[UnisysContext] = Field(None, description="Unisys ePortal context")
    entities_resolved: List[str] = Field(default_factory=list, description="Successfully resolved entities")
    systems_checked: List[str] = Field(default_factory=list, description="Systems that were checked")
    resolution_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall resolution confidence")
    warnings: List[str] = Field(default_factory=list, description="Resolution warnings")
