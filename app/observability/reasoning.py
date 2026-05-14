"""Stage reasoning extraction for observability panels."""

from __future__ import annotations

from typing import Any, Dict, List


def build_stage_reasoning(
    intent: Dict[str, Any] | None = None,
    context: Dict[str, Any] | None = None,
    planner: Dict[str, Any] | None = None,
    execution: Dict[str, Any] | None = None,
    normalization: Dict[str, Any] | None = None,
    federation: Dict[str, Any] | None = None,
) -> Dict[str, List[str]]:
    intent = intent or {}
    context = context or {}
    planner = planner or {}
    execution = execution or {}
    normalization = normalization or {}
    federation = federation or {}

    plan_steps = ((planner.get("plan") or {}).get("steps") or planner.get("steps") or [])
    normalized_summary = normalization.get("summary") or {}
    governance = federation.get("governance") or {}

    return {
        "intent": [
            f"Task classified as {intent.get('task', 'unknown')}.",
            f"Entities resolved from language: {', '.join(intent.get('entities') or []) or 'none'}.",
            f"Intent confidence: {_percent(intent.get('confidence_score'))}.",
        ],
        "context_resolution": [
            f"Systems checked: {', '.join(context.get('systems_checked') or []) or 'none'}.",
            f"Resolved entities: {', '.join(context.get('entities_resolved') or []) or 'none'}.",
            f"Context confidence: {_percent(context.get('resolution_confidence'))}.",
        ],
        "planner": [
            f"Planner produced {len(plan_steps)} execution step(s).",
            f"Mode: {(planner.get('execution_mode') or planner.get('mode') or 'safe_mock')}.",
        ],
        "execution": [
            f"Execution status: {execution.get('status', 'not_run')}.",
            f"Step results returned: {len(execution.get('step_results') or [])}.",
        ],
        "normalization": [
            f"Canonical records produced: {normalized_summary.get('total_records', 0)}.",
            "IBM amounts remain authoritative; Unisys amount is behavioral context.",
        ],
        "federation_intelligence": [
            f"Entity relationships: {len(federation.get('entity_relationships') or [])}.",
            f"Top view: {((federation.get('top_view') or {}).get('view_id') or 'none')}.",
            f"Double-counting protected: {governance.get('double_counting_protected', True)}.",
        ],
    }


def _percent(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{round(value * 100)}%"
    return "N/A"
