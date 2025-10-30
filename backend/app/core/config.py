from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    settings_config: dict[str, Any] = {
        "env_file": (".env", "backend/.env"),
        "env_prefix": "APP_",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }

    app_name: str = "AdamRMS Backend"
    version: str = "0.1.0"
    environment: Literal["development", "staging", "production", "test", "maintenance"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/app.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    jwt_secret_key: str = Field(default="change-me", min_length=8)
    jwt_algorithm: str = "HS256"
    access_token_expiry_minutes: int = 15
    refresh_token_expiry_days: int = 7
    jwt_issuer: str = "adamrms-backend"
    mfa_totp_digits: int = 6
    mfa_totp_interval_seconds: int = 30
    audit_log_path: str = Field(default="backend/var/security_audit.log")
    security_alert_log_path: str = Field(default="backend/var/security_alerts.jsonl")
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"
    celery_fallback_broker_url: str = "memory://"
    celery_fallback_result_backend: str = "cache+memory://"
    celery_default_queue: str = "integrations"
    celery_task_always_eager: bool = False
    celery_beat_schedule_path: str = "backend/app/integrations/schedule.py"
    integration_modes: dict[str, str] = Field(default_factory=dict)
    queue_fallback_enabled: bool = True

    @property
    def access_token_ttl(self) -> timedelta:
        return timedelta(minutes=self.access_token_expiry_minutes)

    @property
    def refresh_token_ttl(self) -> timedelta:
        return timedelta(days=self.refresh_token_expiry_days)

    @property
    def audit_log_file(self) -> Path:
        return Path(self.audit_log_path)

    @property
    def security_alert_file(self) -> Path:
        return Path(self.security_alert_log_path)

    @property
    def beat_schedule_path(self) -> Path:
        return Path(self.celery_beat_schedule_path)

    @property
    def is_debug(self) -> bool:
        return self.debug or self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()


settings = get_settings()
