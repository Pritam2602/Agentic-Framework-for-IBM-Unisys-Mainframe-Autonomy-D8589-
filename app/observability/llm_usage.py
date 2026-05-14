"""LLM token usage and cost tracking."""

from __future__ import annotations

from typing import Any, Dict

from . import utc_now_iso
from .live import publish_event
from .metrics import record_llm_metrics
from .storage import save_llm_usage


# Conservative demo estimates. Adjust to your provider contract if needed.
MODEL_COST_PER_1K_TOKENS = {
    "gemini-2.5-flash-lite": 0.00015,
    "gemini-3-flash-preview": 0.00030,
    "gemini-2.0-flash-lite": 0.00010,
}


def record_llm_usage(
    stage: str,
    model: str,
    response: Any = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    usage = _extract_usage(response)
    total_tokens = usage.get("total_tokens") or (
        (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0)
    )
    rate = MODEL_COST_PER_1K_TOKENS.get(model, 0.0)
    event = {
        "timestamp": utc_now_iso(),
        "stage": stage,
        "model": model,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": total_tokens,
        "estimated_cost_usd": round((total_tokens / 1000) * rate, 8) if total_tokens else 0.0,
        "metadata": metadata or {},
    }
    save_llm_usage(event)
    record_llm_metrics(event)
    publish_event({"type": "llm_usage", **event})
    return event


def _extract_usage(response: Any) -> Dict[str, int]:
    response_metadata = getattr(response, "response_metadata", {}) or {}
    usage_metadata = getattr(response, "usage_metadata", {}) or {}
    candidates = [
        usage_metadata,
        response_metadata.get("usage_metadata", {}),
        response_metadata.get("token_usage", {}),
    ]
    for item in candidates:
        if not isinstance(item, dict):
            continue
        input_tokens = (
            item.get("input_tokens")
            or item.get("prompt_token_count")
            or item.get("prompt_tokens")
            or 0
        )
        output_tokens = (
            item.get("output_tokens")
            or item.get("candidates_token_count")
            or item.get("completion_tokens")
            or 0
        )
        total_tokens = (
            item.get("total_tokens")
            or item.get("total_token_count")
            or (input_tokens + output_tokens)
        )
        if total_tokens:
            return {
                "input_tokens": int(input_tokens or 0),
                "output_tokens": int(output_tokens or 0),
                "total_tokens": int(total_tokens or 0),
            }
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
