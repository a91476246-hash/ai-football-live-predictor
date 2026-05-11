"""Structured logging setup using structlog."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import get_settings


def _drop_color_message_key(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """uvicorn duplicates the color-formatted message; drop it."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """Configure stdlib + structlog. Idempotent."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        _drop_color_message_key,
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
        ],
    )

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Quiet noisy libraries.
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access", "playwright"):
        logging.getLogger(noisy).handlers = [handler]
        logging.getLogger(noisy).propagate = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog-bound logger."""
    return structlog.stdlib.get_logger(name)
