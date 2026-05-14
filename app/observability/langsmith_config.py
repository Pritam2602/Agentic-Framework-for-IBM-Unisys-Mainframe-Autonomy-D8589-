"""Optional LangSmith configuration helpers."""

from __future__ import annotations

import os
from typing import Any, Optional


def langsmith_enabled() -> bool:
    return os.getenv("LANGSMITH_TRACING", "").lower() in {"1", "true", "yes"}


def get_langsmith_client() -> Optional[Any]:
    if not langsmith_enabled():
        return None
    try:
        from langsmith import Client

        return Client()
    except Exception:
        return None


def langsmith_project() -> str:
    return os.getenv("LANGSMITH_PROJECT", "communicator-federation")
