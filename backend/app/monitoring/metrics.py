from __future__ import annotations

from typing import Iterable

HAS_PROMETHEUS = True

try:
    from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest
except ModuleNotFoundError:  # pragma: no cover - fallback for lightweight environments
    HAS_PROMETHEUS = False
    CollectorRegistry = dict  # type: ignore[misc,assignment]

    class _Counter(dict):  # type: ignore[override]
        def labels(self, **kwargs):
            key = tuple(sorted(kwargs.items()))
            self.setdefault(key, 0)

            class _Recorder:
                def __init__(self, store, store_key):
                    self._store = store
                    self._key = store_key

                def inc(self, amount: float = 1.0) -> None:
                    self._store[self._key] = self._store.get(self._key, 0) + amount

            return _Recorder(self, key)

    class _Histogram(dict):
        def labels(self, **kwargs):
            key = tuple(sorted(kwargs.items()))
            self.setdefault(key, [])

            class _Recorder:
                def __init__(self, store, store_key):
                    self._store = store
                    self._key = store_key

                def observe(self, value: float) -> None:
                    self._store[self._key].append(value)

            return _Recorder(self, key)

    class _Gauge(dict):
        def set(self, value: float) -> None:
            self["value"] = value

    _fallback_metric_names = [
        "integration_runs_total",
        "integration_duration_seconds",
        "integration_queue_depth",
    ]

    def generate_latest(registry: CollectorRegistry) -> bytes:  # type: ignore[override]
        return "\n".join(_fallback_metric_names).encode()

    def Counter(*args, **kwargs):  # type: ignore[misc]
        return _Counter()

    def Histogram(*args, **kwargs):  # type: ignore[misc]
        return _Histogram()

    def Gauge(*args, **kwargs):  # type: ignore[misc]
        return _Gauge()

from app.integrations.base import IntegrationResult

_registry = CollectorRegistry()
_integration_runs = Counter(
    "integration_runs_total",
    "Total number of integration executions",
    labelnames=("name", "status"),
    registry=_registry,
)
_integration_duration = Histogram(
    "integration_duration_seconds",
    "Duration of integration execution",
    labelnames=("name",),
    registry=_registry,
)
_queue_depth = Gauge(
    "integration_queue_depth",
    "Approximate depth of the integration queue",
    registry=_registry,
)


def record_integration_result(result: IntegrationResult, duration_seconds: float | None = None) -> None:
    _integration_runs.labels(name=result.name, status=result.status).inc()
    if duration_seconds is not None:
        _integration_duration.labels(name=result.name).observe(duration_seconds)


def set_queue_depth(depth: int) -> None:
    _queue_depth.set(depth)


def get_registry() -> CollectorRegistry:
    return _registry


def render_metrics() -> str:
    if HAS_PROMETHEUS:
        return generate_latest(_registry).decode("utf-8")
    return generate_latest(_registry).decode("utf-8")


def metrics_summary() -> dict[str, object]:
    return {
        "metrics": [
            "integration_runs_total",
            "integration_duration_seconds",
            "integration_queue_depth",
        ]
    }


__all__ = [
    "record_integration_result",
    "set_queue_depth",
    "get_registry",
    "render_metrics",
    "metrics_summary",
]
