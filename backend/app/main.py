from __future__ import annotations
from fastapi import FastAPI

from app.api import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.is_debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

register_middleware(app, settings)
register_exception_handlers(app)

app.include_router(api_router, prefix="/api")


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Return basic API metadata."""

    return {"app": settings.app_name, "version": settings.version}
