from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog

from app.config import Settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def _add_request_id(_: object, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event_dict.setdefault("request_id", request_id_var.get())
    return event_dict


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    base_context = {
        "region": settings.app_region,
        "env": settings.app_env,
        "version": settings.app_version,
    }

    structlog.contextvars.bind_contextvars(**base_context)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _add_request_id,
        timestamper,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=shared_processors,
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(noisy)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
