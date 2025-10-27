from fastapi import APIRouter

from app.api.routes import assets, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(assets.router)

__all__ = ["api_router"]
