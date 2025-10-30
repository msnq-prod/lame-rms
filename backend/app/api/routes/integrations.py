from __future__ import annotations

try:
    from celery.result import AsyncResult  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback when Celery isn't installed yet
    class AsyncResult:  # type: ignore[override]
        def __init__(self, task_id: str, app) -> None:  # noqa: ANN001 - stub
            self.id = task_id
            result = getattr(app, "_results", {}).get(task_id)
            self.state = getattr(result, "state", "SUCCESS")
            self.result = getattr(result, "result", None)

        def ready(self) -> bool:
            return True

        def successful(self) -> bool:
            return True

        def failed(self) -> bool:
            return False
from fastapi import APIRouter, HTTPException, status
from structlog import get_logger

from app.integrations.registry import get_integrations
from app.integrations.tasks import run_integration
from app.monitoring.metrics import set_queue_depth
from app.schemas.integrations import EnqueueResponse, IntegrationInfo, TaskProgress
from app.worker import celery_app

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = get_logger(__name__)

INTEGRATION_DESCRIPTIONS = {
    "crm_sync": "Synchronise contacts from the CRM API",
    "crm_cached": "Reuse cached CRM data as a fallback",
    "notifications": "Dispatch notification digests",
    "object_storage": "Persist integration payloads to object storage",
}


@router.get("/", response_model=list[IntegrationInfo])
async def list_integrations() -> list[IntegrationInfo]:
    return [
        IntegrationInfo(name=name, description=INTEGRATION_DESCRIPTIONS.get(name, name))
        for name in get_integrations()
    ]


@router.post("/{integration_name}/enqueue", response_model=EnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_integration(integration_name: str) -> EnqueueResponse:
    if integration_name not in get_integrations():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown integration")
    async_result = run_integration.delay(integration_name)
    logger.info("integration.enqueue", integration=integration_name, task_id=async_result.id)
    set_queue_depth(1)
    return EnqueueResponse(task_id=async_result.id)


@router.get("/tasks/{task_id}", response_model=TaskProgress)
async def task_status(task_id: str) -> TaskProgress:
    result = AsyncResult(task_id, app=celery_app)
    payload = result.result if isinstance(result.result, dict) else None
    status_text = getattr(result, "status", None)
    if result.failed():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(result.result))
    if result.ready():
        set_queue_depth(0)
    return TaskProgress(
        id=task_id,
        state=result.state,
        status=status_text,
        result=payload if result.successful() else None,
    )


__all__ = ["router"]
