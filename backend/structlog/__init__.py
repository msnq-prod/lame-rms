from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Callable, Iterable, MutableMapping


@dataclass
class _TimeStamper:
    fmt: str = "iso"

    def __call__(self, logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        if self.fmt == "iso":
            event_dict.setdefault("timestamp", datetime.utcnow().isoformat())
        return event_dict


def _identity(logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return event_dict


def _add_log_level(logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    event_dict.setdefault("level", method_name)
    return event_dict


def _json_renderer(logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return event_dict


class _BoundLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def bind(self, **_: Any) -> "_BoundLogger":
        return self

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info("%s %s", event, kwargs if kwargs else "")

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning("%s %s", event, kwargs if kwargs else "")

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error("%s %s", event, kwargs if kwargs else "")

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception("%s %s", event, kwargs if kwargs else "")


class _LoggerFactory:
    def __call__(self) -> logging.Logger:
        return logging.getLogger()


class _StructlogNamespace:
    def __init__(self) -> None:
        self.contextvars = SimpleNamespace(merge_contextvars=_identity)
        self.processors = SimpleNamespace(
            TimeStamper=_TimeStamper,
            add_log_level=_add_log_level,
            StackInfoRenderer=lambda: _identity,
            format_exc_info=_identity,
            UnicodeDecoder=lambda: _identity,
            JSONRenderer=lambda: _json_renderer,
        )
        self.stdlib = SimpleNamespace(
            BoundLogger=_BoundLogger,
            LoggerFactory=_LoggerFactory,
            PositionalArgumentsFormatter=lambda: _identity,
        )

    def configure(
        self,
        processors: Iterable[Callable[[logging.Logger, str, MutableMapping[str, Any]], MutableMapping[str, Any]]],
        wrapper_class: type[_BoundLogger] | None = None,
        logger_factory: Callable[[], logging.Logger] | None = None,
        cache_logger_on_first_use: bool = True,
    ) -> None:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    def get_logger(self, name: str | None = None) -> _BoundLogger:
        return _BoundLogger(logging.getLogger(name))


_structlog = _StructlogNamespace()

configure = _structlog.configure
get_logger = _structlog.get_logger
contextvars = _structlog.contextvars
processors = _structlog.processors
stdlib = _structlog.stdlib

__all__ = ["configure", "get_logger", "contextvars", "processors", "stdlib"]
