from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.integrations.base import Integration, IntegrationResult


class NotificationIntegration(Integration):
    """Write notification events to a mailbox file to simulate external delivery."""

    name = "notifications"

    def __init__(self, *, mailbox_path: Path | None = None) -> None:
        settings = get_settings()
        default_mailbox = mailbox_path or Path(settings.audit_log_file).parent / "integrations" / "notifications.log"
        default_mailbox.parent.mkdir(parents=True, exist_ok=True)
        self.mailbox_path = default_mailbox

    def execute(self, *, payload: dict[str, Any] | None = None) -> IntegrationResult:
        payload = payload or {"message": "Integration notification"}
        self.mailbox_path.write_text(payload.get("message", "Notification"), encoding="utf-8")
        return IntegrationResult(
            name=self.name,
            status="ok",
            detail="Notification delivered",
            metadata={"mailbox": str(self.mailbox_path)},
        )


__all__ = ["NotificationIntegration"]
