from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.health import get_health_status


class HealthResponse(BaseModel):
    status: str


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def read_health() -> HealthResponse:
    """Return application health status."""

    return HealthResponse(status=get_health_status())
