from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.integrations.base import Integration, IntegrationResult


class ObjectStorageIntegration(Integration):
    """Persist integration payloads to a local object storage directory."""

    name = "object_storage"

    def __init__(self, *, storage_root: Path | None = None) -> None:
        settings = get_settings()
        default_root = storage_root or Path(settings.audit_log_file).parent / "integrations" / "objects"
        default_root.mkdir(parents=True, exist_ok=True)
        self.storage_root = default_root

    def execute(self, *, payload: dict[str, Any] | None = None) -> IntegrationResult:
        payload = payload or {}
        filename = payload.get("filename", "payload.json")
        target = self.storage_root / filename
        target.write_text("{}\n" if not payload else repr(payload), encoding="utf-8")
        return IntegrationResult(
            name=self.name,
            status="ok",
            detail="Payload stored in object storage",
            metadata={"path": str(target)},
        )


__all__ = ["ObjectStorageIntegration"]
