from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings


class FeatureFlagState(BaseModel):
    """Declarative configuration for backend feature flags."""

    model_config = ConfigDict(extra="allow")

    assets_api: bool = True

    def is_enabled(self, flag: str) -> bool:
        return bool(getattr(self, flag, False))


DEFAULT_FLAGS = FeatureFlagState()


@lru_cache(maxsize=1)
def get_feature_flags() -> FeatureFlagState:
    """Return cached feature flag configuration merged with overrides."""

    settings = get_settings()
    overrides: dict[str, Any] = {}
    raw_overrides = getattr(settings, "feature_flags", {})
    if isinstance(raw_overrides, dict):
        overrides = raw_overrides
    merged = {**DEFAULT_FLAGS.model_dump(), **overrides}
    return FeatureFlagState(**merged)


def is_enabled(flag: str) -> bool:
    """Return True when *flag* is enabled."""

    return get_feature_flags().is_enabled(flag)


def ensure_feature(flag: str):
    """FastAPI dependency ensuring that *flag* is enabled."""

    def dependency() -> None:
        if not is_enabled(flag):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Feature '{flag}' is temporarily unavailable.",
            )

    return dependency


__all__ = [
    "FeatureFlagState",
    "DEFAULT_FLAGS",
    "get_feature_flags",
    "is_enabled",
    "ensure_feature",
]
