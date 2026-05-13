"""
utils.py - Utility functions for priority and confidence
"""

from typing import Any, Dict
from .constants import TASK_KEYWORDS


def infer_priority(task: str) -> str:
    """Infer priority from task type"""
    if task in ["compare", "analyze"]:
        return "high"
    elif task == "fetch":
        return "medium"
    elif task in ["reconcile", "transform", "discover"]:
        return "medium"
    return "low"


def compute_confidence(data: Dict[str, Any]) -> float:
    """Compute confidence based on data completeness and clarity"""
    score = 0.5  # baseline
    
    if data.get("entities"):
        score += 0.15
    else:
        return 0.3  # cannot function without entities
    
    if data.get("attributes"):
        score += 0.15
    
    filters = data.get("filters", {})
    if filters.get("time_range") or filters.get("conditions"):
        score += 0.1
    
    if data.get("systems"):
        score += 0.1
    
    # Reduce confidence if task is ambiguous
    if data.get("task") not in TASK_KEYWORDS:
        score -= 0.2
    
    return min(max(score, 0.0), 1.0)
