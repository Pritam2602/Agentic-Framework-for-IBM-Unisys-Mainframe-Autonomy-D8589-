"""Mock z/OS API endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.mock_zos import MockZOSSimulator

router = APIRouter(prefix="/api/mock-zos", tags=["mock-zos"])


class MockZOSCommandRequest(BaseModel):
    """Request body for mock z/OS command execution."""

    command: str = Field(description="Zowe command string to simulate")
    parameters: Dict[str, Any] = Field(default_factory=dict)


@router.post("/execute")
async def execute_mock_zos_command(request: MockZOSCommandRequest) -> Dict[str, Any]:
    """Execute a safe mock Zowe command against local z/OS simulation data."""
    try:
        simulator = MockZOSSimulator()
        return simulator.execute(request.command, request.parameters)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health")
async def mock_zos_health() -> Dict[str, Any]:
    """Mock z/OS health check."""
    simulator = MockZOSSimulator()
    return {
        "status": "healthy",
        "service": "mock-zos",
        "mode": "safe_mock",
        "supported_command_families": [
            "zowe files view ds",
            "zowe files list ds",
            "zowe zos-jobs submit",
            "zowe zos-jobs list/view",
            "zowe zos-workflows list/view",
            "zowe zosmf info",
        ],
        "datasets": list(simulator.datasets.keys()),
    }
