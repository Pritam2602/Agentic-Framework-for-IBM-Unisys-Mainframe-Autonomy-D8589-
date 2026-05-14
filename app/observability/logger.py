"""Structured logging setup with optional structlog support."""

from __future__ import annotations

import logging
import sys
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    try:
        import structlog

        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    except Exception:
        logging.getLogger(__name__).debug("structlog unavailable; using standard logging")


def get_logger(name: str) -> Any:
    try:
        import structlog

        return structlog.get_logger(name)
    except Exception:
        return logging.getLogger(name)
