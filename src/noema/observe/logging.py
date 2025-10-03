"""Structured logging helpers."""

from __future__ import annotations

import logging

import structlog


def configure_logging(run_id: str) -> None:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.getLogger().setLevel(logging.INFO)
    structlog.get_logger().bind(run_id=run_id)


def log_tick(run_id: str, tick: int, message: str, **extra: object) -> None:
    logger = structlog.get_logger()
    logger.info(message, run_id=run_id, tick=tick, **extra)


__all__ = ["configure_logging", "log_tick"]
