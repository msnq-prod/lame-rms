from __future__ import annotations

from typing import Any

from structlog import get_logger

from app.integrations import run_with_fallback
from app.integrations.crm import CRMIntegration, CachedCRMIntegration
from app.integrations.notifications import NotificationIntegration
from app.integrations.registry import instantiate
from app.integrations.storage import ObjectStorageIntegration
from app.monitoring.metrics import record_integration_result
from app.worker import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.integrations.tasks.run_integration", bind=True)
def run_integration(self, integration_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    logger.info("integration.task.start", integration=integration_name)
    integration = instantiate(integration_name)
    fallback = CachedCRMIntegration() if integration_name == "crm_sync" else None
    result = run_with_fallback(integration, payload=payload, fallback=fallback)
    record_integration_result(result)
    logger.info("integration.task.completed", integration=integration_name, status=result.status)
    return result.to_dict()


@celery_app.task(name="app.integrations.tasks.run_crm_sync")
def run_crm_sync() -> dict[str, Any]:
    result = run_with_fallback(CRMIntegration(), fallback=CachedCRMIntegration())
    record_integration_result(result)
    return result.to_dict()


@celery_app.task(name="app.integrations.tasks.archive_storage_snapshot")
def archive_storage_snapshot() -> dict[str, Any]:
    payload = {"filename": "snapshot.txt"}
    result = ObjectStorageIntegration().execute(payload=payload)
    record_integration_result(result)
    return result.to_dict()


@celery_app.task(name="app.integrations.tasks.deliver_notifications")
def deliver_notifications() -> dict[str, Any]:
    result = NotificationIntegration().execute(payload={"message": "Scheduled digest sent"})
    record_integration_result(result)
    return result.to_dict()


__all__ = [
    "run_integration",
    "run_crm_sync",
    "archive_storage_snapshot",
    "deliver_notifications",
]
