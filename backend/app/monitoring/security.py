from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SecurityEvent:
    event_type: str
    severity: str
    payload: dict[str, Any]
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class SecurityAlert:
    title: str
    severity: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SecurityMonitor:
    """Collects security events and writes alerts to JSONL logs."""

    def __init__(self, log_path: Path | str) -> None:
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._alerts: list[SecurityAlert] = []
        self._events: list[SecurityEvent] = []

    def emit_alert(self, title: str, severity: str, payload: dict[str, Any] | None = None) -> SecurityAlert:
        alert = SecurityAlert(
            title=title,
            severity=severity,
            payload=payload or {},
        )
        self._alerts.append(alert)
        self._write_record({"kind": "alert", **self._serialize_alert(alert)})
        return alert

    def record_event(self, event_type: str, *, severity: str, payload: dict[str, Any] | None = None) -> SecurityEvent:
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            payload=payload or {},
        )
        self._events.append(event)
        self._write_record({"kind": "event", **self._serialize_event(event)})
        return event

    def load_alerts(self) -> list[SecurityAlert]:
        return list(self._alerts)

    def load_events(self) -> list[SecurityEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._alerts.clear()
        self._events.clear()
        if self._log_path.exists():
            self._log_path.unlink()

    def _serialize_alert(self, alert: SecurityAlert) -> dict[str, Any]:
        return {
            "title": alert.title,
            "severity": alert.severity,
            "payload": alert.payload,
            "created_at": alert.created_at.isoformat(),
        }

    def _serialize_event(self, event: SecurityEvent) -> dict[str, Any]:
        return {
            "event_type": event.event_type,
            "severity": event.severity,
            "payload": event.payload,
            "recorded_at": event.recorded_at.isoformat(),
        }

    def _write_record(self, payload: dict[str, Any]) -> None:
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


__all__ = ["SecurityMonitor", "SecurityEvent", "SecurityAlert"]
