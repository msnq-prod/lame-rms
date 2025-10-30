from fastapi import APIRouter

from app.api.routes import assets, health, integrations

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(assets.router)
api_router.include_router(integrations.router)

__all__ = ["api_router"]
