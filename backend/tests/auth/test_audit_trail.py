from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.auth.audit import AuditTrail
from app.auth.models import AuditEvent
from app.monitoring.security import SecurityMonitor


def test_audit_trail_persists_events() -> None:
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.log"
        monitor = SecurityMonitor(Path(tmpdir) / "alerts.jsonl")
        trail = AuditTrail(log_path, monitor)
        event = AuditEvent(event_type="auth.login", user_id="user-1", actor="user@example.com", severity="info")
        trail.record(event)
        stored = trail.load()
        assert len(stored) == 1
        assert stored[0].event_type == "auth.login"


def test_audit_trail_emits_alert_for_high_severity() -> None:
    with TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "audit.log"
        monitor = SecurityMonitor(Path(tmpdir) / "alerts.jsonl")
        trail = AuditTrail(log_path, monitor)
        event = AuditEvent(event_type="auth.lockout", severity="high", metadata={"user": "user-1"})
        trail.record(event)
        alerts = monitor.load_alerts()
        assert alerts and alerts[0].severity == "high"
