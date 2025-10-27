from app.core.config import get_settings


def get_health_status() -> str:
    """Return the current service health indicator."""

    settings = get_settings()
    return "ok" if settings.environment != "maintenance" else "degraded"


__all__ = ["get_health_status"]
