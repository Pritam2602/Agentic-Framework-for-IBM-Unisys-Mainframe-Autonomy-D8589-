"""Optional LangSmith tracing wrappers.

The helpers are no-ops when LangSmith is not installed or not enabled.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Iterator, TypeVar

from .langsmith_config import langsmith_enabled


F = TypeVar("F", bound=Callable[..., Any])


def traceable(name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        if not langsmith_enabled():
            return func
        try:
            from langsmith import traceable as langsmith_traceable

            return langsmith_traceable(name=name)(func)  # type: ignore[return-value]
        except Exception:
            return func

    return decorator


@contextmanager
def trace_context(name: str, **metadata: Any) -> Iterator[None]:
    if not langsmith_enabled():
        yield
        return
    try:
        from langsmith import trace

        with trace(name, metadata=metadata):
            yield
    except Exception:
        yield
