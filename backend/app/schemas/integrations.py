from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IntegrationInfo(BaseModel):
    name: str
    description: str


class IntegrationRunResult(BaseModel):
    name: str
    status: str
    detail: str
    executed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnqueueResponse(BaseModel):
    task_id: str
    queued: bool = True


class TaskProgress(BaseModel):
    id: str
    state: str
    status: str | None = None
    result: dict[str, Any] | None = None


__all__ = [
    "IntegrationInfo",
    "IntegrationRunResult",
    "EnqueueResponse",
    "TaskProgress",
]

SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "IntegrationInfo": IntegrationInfo,
    "IntegrationRunResult": IntegrationRunResult,
    "EnqueueResponse": EnqueueResponse,
    "TaskProgress": TaskProgress,
}
