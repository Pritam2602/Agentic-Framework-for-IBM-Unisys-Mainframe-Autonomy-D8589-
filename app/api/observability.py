"""Observability API endpoints for pipeline telemetry."""

from __future__ import annotations

from fastapi import APIRouter, Response
from starlette.responses import StreamingResponse

from app.observability import observability_store
from app.observability.live import event_stream, recent_events
from app.observability.metrics import metrics_response
from app.observability.storage import load_llm_usage


router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/summary")
async def observability_summary():
    """Return aggregate pipeline observability metrics."""
    return observability_store.summary()


@router.get("/runs")
async def recent_observability_runs(limit: int = 20):
    """Return recent pipeline telemetry runs."""
    return {"runs": observability_store.recent_runs(limit=limit)}


@router.get("/events")
async def recent_observability_events(limit: int = 50):
    """Return recent live observability events."""
    return {"events": recent_events(limit=limit)}


@router.get("/stream")
async def observability_stream():
    """Stream live observability events via Server-Sent Events."""
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/llm-usage")
async def llm_usage(limit: int = 50):
    """Return persisted LLM token/cost usage entries."""
    return {"usage": load_llm_usage(limit=limit)}


@router.get("/metrics")
async def prometheus_metrics():
    """Return a lightweight Prometheus-compatible metrics snapshot."""
    content, media_type = metrics_response()
    return Response(
        content=content,
        media_type=media_type,
    )
