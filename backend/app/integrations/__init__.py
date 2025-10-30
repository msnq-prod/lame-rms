"""Integrations with external services and third-party APIs."""

from .base import Integration, IntegrationError, IntegrationResult, run_with_fallback
from .crm import CRMIntegration, CachedCRMIntegration
from .notifications import NotificationIntegration
from .registry import get_integrations, instantiate
from .storage import ObjectStorageIntegration

__all__ = [
    "Integration",
    "IntegrationError",
    "IntegrationResult",
    "run_with_fallback",
    "CRMIntegration",
    "CachedCRMIntegration",
    "NotificationIntegration",
    "ObjectStorageIntegration",
    "get_integrations",
    "instantiate",
]
