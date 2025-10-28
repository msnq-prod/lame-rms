from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.monitoring.security import SecurityMonitor


def test_monitor_records_events_and_alerts() -> None:
    with TemporaryDirectory() as tmpdir:
        monitor = SecurityMonitor(Path(tmpdir) / "alerts.jsonl")
        monitor.record_event("auth.login", severity="info", payload={"user": "user-1"})
        monitor.emit_alert("Suspicious login", severity="high", payload={"ip": "1.2.3.4"})
        events = monitor.load_events()
        alerts = monitor.load_alerts()
        assert len(events) == 1
        assert events[0].event_type == "auth.login"
        assert len(alerts) == 1
        assert alerts[0].title == "Suspicious login"
        log_path = Path(tmpdir) / "alerts.jsonl"
        assert log_path.exists()
        contents = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(contents) == 2
