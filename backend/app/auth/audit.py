from __future__ import annotations

import json
from pathlib import Path

from .models import AuditEvent
from app.monitoring.security import SecurityMonitor


class AuditTrail:
    """Persist audit events to disk and forward alerts."""

    def __init__(self, log_path: Path, monitor: SecurityMonitor | None = None) -> None:
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._monitor = monitor

    def record(self, event: AuditEvent) -> None:
        """Append ``event`` to the audit log and forward critical alerts."""

        line = json.dumps(event.model_dump(mode="json"), ensure_ascii=False)
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        if self._monitor and event.severity in {"high", "critical"}:
            self._monitor.emit_alert(
                title=f"{event.event_type} by {event.actor or 'unknown'}",
                severity=event.severity,
                payload=event.metadata,
            )

    def load(self) -> list[AuditEvent]:
        """Return events parsed from the audit log."""

        if not self._log_path.exists():
            return []
        events = []
        with self._log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    events.append(AuditEvent(**payload))
                except json.JSONDecodeError:
                    continue
        return events


__all__ = ["AuditTrail"]
