from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.services.health import get_health_status
from app.monitoring.metrics import render_metrics


class HealthResponse(BaseModel):
    status: str


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def read_health() -> HealthResponse:
    """Return application health status."""

    return HealthResponse(status=get_health_status())


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    """Expose Prometheus metrics."""

    payload = render_metrics()
    return PlainTextResponse(content=payload, media_type="text/plain; version=0.0.4")
