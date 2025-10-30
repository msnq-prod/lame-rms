from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


class IntegrationError(RuntimeError):
    """Raised when an integration is unable to complete successfully."""


@dataclass(slots=True)
class IntegrationResult:
    """Standard payload describing the outcome of an integration execution."""

    name: str
    status: str
    detail: str
    metadata: dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
            "metadata": self.metadata,
            "executed_at": self.executed_at.isoformat(),
        }


class Integration(Protocol):
    """Public contract for integration adapters."""

    name: str

    def execute(self, *, payload: dict[str, Any] | None = None) -> IntegrationResult:
        """Run the integration and return a :class:`IntegrationResult`."""


def run_with_fallback(
    primary: Integration,
    *,
    payload: dict[str, Any] | None = None,
    fallback: Integration | None = None,
) -> IntegrationResult:
    """Execute an integration with optional fallback logic."""

    try:
        return primary.execute(payload=payload)
    except IntegrationError as exc:
        if fallback is None:
            raise
        metadata = {
            "primary_error": str(exc),
            "fallback": fallback.name,
        }
        fallback_result = fallback.execute(payload=payload)
        fallback_result.metadata.update(metadata)
        fallback_result.detail = f"Fallback executed after primary failure: {fallback_result.detail}"
        return fallback_result
