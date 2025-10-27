"""Service layer entry point for reusable business logic."""

from app.services.health import get_health_status

__all__ = ["get_health_status"]
