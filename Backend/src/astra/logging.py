from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

from astra.config import Settings


request_id_var: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)

ingestion_id_var: ContextVar[str | None] = ContextVar(
    "ingestion_id",
    default=None,
)

repo_var: ContextVar[str | None] = ContextVar(
    "repo",
    default=None,
)


def _add_context(
    _: Any,
    __: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:

    for var in (
        request_id_var,
        ingestion_id_var,
        repo_var,
    ):
        value = var.get()

        if value is not None and var.name not in event_dict:
            event_dict[var.name] = value

    return event_dict


def configure_logging(settings: Settings) -> None:

    timestamper = structlog.processors.TimeStamper(
        fmt="iso",
        utc=True,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _add_context,
        timestamper,
    ]

    if settings.log_json:
        renderer: structlog.types.Processor = (
            structlog.processors.JSONRenderer()
        )
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=False,
        )

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    root = logging.getLogger()

    root.handlers = [handler]

    root.setLevel(
        getattr(logging, settings.log_level)
    )


def get_logger(
    name: str | None = None,
) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)