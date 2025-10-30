from __future__ import annotations

from contextlib import suppress
from typing import Any, Callable

try:
    from celery import Celery as CeleryBase
    from kombu.exceptions import KombuError
    HAS_CELERY = True
except ModuleNotFoundError:  # pragma: no cover - lightweight fallback
    HAS_CELERY = False

    class KombuError(Exception):
        """Placeholder kombu error when Celery is unavailable."""

    class CeleryBase:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.conf: dict[str, Any] = {}
            self._tasks: dict[str, Callable[..., Any]] = {}
            self._results: dict[str, Any] = {}

        def task(self, name: str | None = None, bind: bool = False, **_: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                task_name = name or func.__name__
                self._tasks[task_name] = func

                def delay(*args: Any, **kwargs: Any) -> "StubAsyncResult":
                    if bind:
                        result = func(None, *args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    async_result = StubAsyncResult(result)
                    self._results[async_result.id] = async_result
                    return async_result

                func.delay = delay  # type: ignore[attr-defined]
                return func

            return decorator

        def autodiscover_tasks(self, *_: Any, **__: Any) -> None:  # pragma: no cover - no-op
            return None

        def connection(self) -> "StubConnection":
            return StubConnection()

    class StubConnection:
        def ensure_connection(self, **_: Any) -> None:  # pragma: no cover - always ok
            return None

        def __enter__(self) -> "StubConnection":
            return self

        def __exit__(self, *exc: Any) -> None:
            return None

    class StubAsyncResult:
        def __init__(self, result: Any) -> None:
            from uuid import uuid4

            self.id = str(uuid4())
            self.result = result
            self.state = "SUCCESS"

        def ready(self) -> bool:
            return True

        def successful(self) -> bool:
            return True

        def failed(self) -> bool:
            return False

    Celery = CeleryBase
else:
    Celery = CeleryBase
    from uuid import uuid4

    class StubAsyncResult:
        def __init__(self, result: Any) -> None:
            self.id = str(uuid4())
            self.result = result
            self.state = "SUCCESS"

        def ready(self) -> bool:
            return True

        def successful(self) -> bool:
            return True

        def failed(self) -> bool:
            return False

from structlog import get_logger

from app.core.config import get_settings
from app.integrations.schedule import get_beat_schedule
from app.monitoring.metrics import set_queue_depth

logger = get_logger(__name__)


def _configure(app: Celery) -> None:
    settings = get_settings()
    app.conf.update(
        task_default_queue=settings.celery_default_queue,
        task_track_started=True,
        result_extended=True,
        beat_schedule=get_beat_schedule(),
    )


def create_celery() -> Celery:
    settings = get_settings()
    primary = Celery(
        "app",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.integrations.tasks"],
    )
    _configure(primary)
    try:
        with primary.connection() as connection:
            connection.ensure_connection(max_retries=1)
        logger.info("celery.broker.connected", broker=settings.celery_broker_url)
        app = primary
    except KombuError as exc:
        if not settings.queue_fallback_enabled:
            raise
        logger.warning("celery.broker.fallback", error=str(exc))
        fallback = Celery(
            "app",
            broker=settings.celery_fallback_broker_url,
            backend=settings.celery_fallback_result_backend,
            include=["app.integrations.tasks"],
        )
        _configure(fallback)
        fallback.conf.task_always_eager = True
        fallback.conf.task_eager_propagates = True
        app = fallback
    app.autodiscover_tasks()
    with suppress(Exception):
        set_queue_depth(0)
    return app


celery_app = create_celery()

__all__ = ["celery_app", "create_celery"]
