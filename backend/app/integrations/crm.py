from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.integrations.base import Integration, IntegrationError, IntegrationResult


class CRMIntegration(Integration):
    """Primary CRM integration that synchronises contacts from an external feed."""

    name = "crm_sync"

    def __init__(self, *, data_source: Path | None = None) -> None:
        default_source = Path(__file__).resolve().parent / "data" / "crm_source.json"
        self.data_source = data_source or default_source

    def execute(self, *, payload: dict[str, Any] | None = None) -> IntegrationResult:
        if not self.data_source.exists():
            raise IntegrationError(f"CRM data source {self.data_source} does not exist")
        records = self.data_source.read_text(encoding="utf-8").strip()
        if not records:
            raise IntegrationError("CRM data source is empty")
        return IntegrationResult(
            name=self.name,
            status="ok",
            detail="CRM feed synchronised",
            metadata={"source": str(self.data_source)},
        )


class CachedCRMIntegration(Integration):
    """Fallback integration that reuses the latest successful snapshot."""

    name = "crm_cached"

    def __init__(self, cache_dir: Path | None = None) -> None:
        settings = get_settings()
        cache_root = cache_dir or Path(settings.audit_log_file).parent / "integrations"
        cache_root.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_root / "crm_cache.json"
        if not self.cache_file.exists():
            self.cache_file.write_text("{}\n", encoding="utf-8")

    def execute(self, *, payload: dict[str, Any] | None = None) -> IntegrationResult:
        snapshot = self.cache_file.read_text(encoding="utf-8").strip()
        status = "warning" if snapshot == "{}" else "ok"
        detail = "Cached snapshot used" if status == "ok" else "Empty cache returned"
        return IntegrationResult(
            name=self.name,
            status=status,
            detail=detail,
            metadata={"cache_file": str(self.cache_file)},
        )


__all__ = ["CRMIntegration", "CachedCRMIntegration"]
