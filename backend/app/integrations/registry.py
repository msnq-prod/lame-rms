from __future__ import annotations

from collections.abc import Callable

from app.integrations.base import Integration
from app.integrations.crm import CRMIntegration, CachedCRMIntegration
from app.integrations.notifications import NotificationIntegration
from app.integrations.storage import ObjectStorageIntegration

IntegrationFactory = Callable[[], Integration]


def get_integrations() -> dict[str, IntegrationFactory]:
    """Return the catalog of available integration factories."""

    return {
        "crm_sync": CRMIntegration,
        "crm_cached": CachedCRMIntegration,
        "notifications": NotificationIntegration,
        "object_storage": ObjectStorageIntegration,
    }


def instantiate(name: str) -> Integration:
    try:
        factory = get_integrations()[name]
    except KeyError as exc:
        raise KeyError(f"Unknown integration '{name}'") from exc
    return factory()


__all__ = ["get_integrations", "instantiate"]
