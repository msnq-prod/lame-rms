from __future__ import annotations

from functools import lru_cache
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

    @property
    def is_debug(self) -> bool:
        return self.debug or self.environment == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()


settings = get_settings()
