import logging
import sys

import structlog


def _get_log_level(log_level: str) -> int:
    level = getattr(logging, log_level.upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog-based logging for the application."""

    logging.basicConfig(
        level=_get_log_level(log_level),
        format="%(message)s",
        stream=sys.stdout,
    )

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.getLogger("uvicorn").setLevel(_get_log_level(log_level))
    logging.getLogger("uvicorn.error").setLevel(_get_log_level(log_level))
    logging.getLogger("uvicorn.access").setLevel(_get_log_level(log_level))


__all__ = ["configure_logging"]
