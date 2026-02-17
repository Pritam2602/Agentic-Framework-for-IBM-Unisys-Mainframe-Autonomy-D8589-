"""
Utility helper functions
"""
from typing import Any, Dict
from datetime import datetime


def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO string"""
    return dt.isoformat()


def safe_get(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get value from dictionary"""
    return d.get(key, default)
