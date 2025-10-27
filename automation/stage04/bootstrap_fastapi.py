from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Iterable

FASTAPI_FILES: dict[str, str] = {
    "backend/app/core/config.py": '''
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
''',
    "backend/app/core/logging.py": '''
import logging
import sys

import structlog


def _get_log_level(log_level: str) -> int:
    level = getattr(logging, log_level.upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog-based logging for the application."""

    logging.basicConfig(
        level=_get_log_level(log_level),
        format="%(message)s",
        stream=sys.stdout,
    )

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.getLogger("uvicorn").setLevel(_get_log_level(log_level))
    logging.getLogger("uvicorn.error").setLevel(_get_log_level(log_level))
    logging.getLogger("uvicorn.access").setLevel(_get_log_level(log_level))


__all__ = ["configure_logging"]
''',
    "backend/app/core/middleware.py": '''
from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import Settings


def register_middleware(app: FastAPI, settings: Settings) -> None:
    """Attach common middleware to the FastAPI application."""

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=600,
    )
    app.add_middleware(GZipMiddleware, minimum_size=512)

    trusted_hosts = ["*"] if "*" in settings.cors_origins else ["localhost", "127.0.0.1"]
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)


__all__ = ["register_middleware"]
''',
    "backend/app/core/exceptions.py": '''
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

import structlog

logger = structlog.get_logger(__name__)


class ApplicationError(RuntimeError):
    """Base exception for expected application errors."""

    def __init__(self, message: str, *, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for the FastAPI app."""

    @app.exception_handler(ApplicationError)  # type: ignore[misc]
    async def handle_application_error(request: Request, exc: ApplicationError) -> JSONResponse:
        logger.warning("application_error", path=request.url.path, detail=exc.message)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)  # type: ignore[misc]
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected_error", path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


__all__ = ["ApplicationError", "register_exception_handlers"]
''',
    "backend/app/api/__init__.py": '''
from app.api.routes import api_router

__all__ = ["api_router"]
''',
    "backend/app/api/routes/__init__.py": '''
from fastapi import APIRouter

from app.api.routes import health

api_router = APIRouter()
api_router.include_router(health.router)

__all__ = ["api_router"]
''',
    "backend/app/api/routes/health.py": '''
from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services.health import get_health_status


class HealthResponse(BaseModel):
    status: str


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def read_health() -> HealthResponse:
    """Return application health status."""

    return HealthResponse(status=get_health_status())
''',
    "backend/app/services/__init__.py": '''
"""Service layer entry point for reusable business logic."""

from app.services.health import get_health_status

__all__ = ["get_health_status"]
''',
    "backend/app/services/health.py": '''
from app.core.config import get_settings


def get_health_status() -> str:
    """Return the current service health indicator."""

    settings = get_settings()
    return "ok" if settings.environment != "maintenance" else "degraded"


__all__ = ["get_health_status"]
''',
    "backend/app/repositories/__init__.py": '''
"""Repository layer for database access abstractions."""
''',
    "backend/app/auth/__init__.py": '''
"""Authentication and authorization utilities."""
''',
    "backend/app/integrations/__init__.py": '''
"""Integrations with external services and third-party APIs."""
''',
    "backend/app/main.py": '''
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
''',
    "backend/app/db/session.py": '''
from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()

default_database_url = settings.database_url

if default_database_url.startswith("sqlite"):
    database_path = default_database_url.split("///")[-1]
    if database_path:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(default_database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "engine", "SessionLocal", "get_db"]
''',
    "backend/pydantic_settings/__init__.py": '''
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel

SettingsConfigDict = dict[str, Any]


def _read_env_file(path: Path, encoding: str = "utf-8") -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw_line in path.read_text(encoding=encoding).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


class BaseSettings(BaseModel):
    """Minimal BaseSettings implementation compatible with Pydantic v2."""

    settings_config: SettingsConfigDict = {}

    def __init__(self, **data: Any) -> None:
        merged = {**self.__class__._load_env(), **data}
        super().__init__(**merged)

    @classmethod
    def _load_env(cls) -> dict[str, Any]:
        config = getattr(cls, "settings_config", {})
        env_prefix: str = config.get("env_prefix", "")
        case_sensitive: bool = config.get("case_sensitive", False)
        encoding: str = config.get("env_file_encoding", "utf-8")
        env_files_cfg = config.get("env_file")
        env_files: Iterable[str]
        if env_files_cfg is None:
            env_files = []
        elif isinstance(env_files_cfg, (str, Path)):
            env_files = [str(env_files_cfg)]
        else:
            env_files = [str(item) for item in env_files_cfg]

        file_env: dict[str, str] = {}
        for env_file in env_files:
            file_env.update(_read_env_file(Path(env_file), encoding=encoding))

        combined_env: dict[str, str] = {**file_env, **os.environ}
        values: dict[str, Any] = {}
        for field_name in cls.model_fields:
            if case_sensitive:
                candidates = [f"{env_prefix}{field_name}"]
            else:
                key = f"{env_prefix}{field_name}".upper()
                candidates = [key, key.lower(), key.replace("-", "_")]
            for candidate in candidates:
                if candidate in combined_env:
                    values[field_name] = combined_env[candidate]
                    break
        return values


__all__ = ["BaseSettings", "SettingsConfigDict"]
''',
    "backend/structlog/__init__.py": '''
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Callable, Iterable, MutableMapping


@dataclass
class _TimeStamper:
    fmt: str = "iso"

    def __call__(self, logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        if self.fmt == "iso":
            event_dict.setdefault("timestamp", datetime.utcnow().isoformat())
        return event_dict


def _identity(logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return event_dict


def _add_log_level(logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    event_dict.setdefault("level", method_name)
    return event_dict


def _json_renderer(logger: logging.Logger, method_name: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    return event_dict


class _BoundLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def bind(self, **_: Any) -> "_BoundLogger":
        return self

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info("%s %s", event, kwargs if kwargs else "")

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning("%s %s", event, kwargs if kwargs else "")

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error("%s %s", event, kwargs if kwargs else "")

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception("%s %s", event, kwargs if kwargs else "")


class _LoggerFactory:
    def __call__(self) -> logging.Logger:
        return logging.getLogger()


class _StructlogNamespace:
    def __init__(self) -> None:
        self.contextvars = SimpleNamespace(merge_contextvars=_identity)
        self.processors = SimpleNamespace(
            TimeStamper=_TimeStamper,
            add_log_level=_add_log_level,
            StackInfoRenderer=lambda: _identity,
            format_exc_info=_identity,
            UnicodeDecoder=lambda: _identity,
            JSONRenderer=lambda: _json_renderer,
        )
        self.stdlib = SimpleNamespace(
            BoundLogger=_BoundLogger,
            LoggerFactory=_LoggerFactory,
            PositionalArgumentsFormatter=lambda: _identity,
        )

    def configure(
        self,
        processors: Iterable[Callable[[logging.Logger, str, MutableMapping[str, Any]], MutableMapping[str, Any]]],
        wrapper_class: type[_BoundLogger] | None = None,
        logger_factory: Callable[[], logging.Logger] | None = None,
        cache_logger_on_first_use: bool = True,
    ) -> None:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    def get_logger(self, name: str | None = None) -> _BoundLogger:
        return _BoundLogger(logging.getLogger(name))


_structlog = _StructlogNamespace()

configure = _structlog.configure
get_logger = _structlog.get_logger
contextvars = _structlog.contextvars
processors = _structlog.processors
stdlib = _structlog.stdlib

__all__ = ["configure", "get_logger", "contextvars", "processors", "stdlib"]
''',
    "backend/tests/api/__init__.py": '''
"""API layer tests."""
''',
    "backend/tests/api/test_health.py": '''
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
''',
    "backend/requirements.txt": '''
fastapi>=0.115,<0.116
uvicorn[standard]>=0.30,<0.31
SQLAlchemy>=2.0,<3.0
psycopg[binary]>=3.1,<3.2
pydantic>=2.8,<3.0
pydantic-settings>=2.4,<3.0
structlog>=24.1,<25.0
alembic>=1.13,<1.14
passlib[bcrypt]>=1.7,<1.8
PyJWT>=2.9,<3.0
httpx>=0.27,<0.28
pytest>=8.0,<9.0
pytest-cov>=4.1,<5.0
mypy>=1.10,<2.0
ruff>=0.6.0,<0.7.0
''',
    "backend/.pre-commit-config.yaml": '''
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.6.4
    hooks:
      - id: ruff
        args: ["--fix"]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: ["pydantic", "pydantic-settings", "sqlalchemy"]
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        additional_dependencies: ["flake8-bugbear"]
''',
    "backend/pyproject.toml": '''
[build-system]
requires = ["setuptools>=67", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lame-rms-backend"
version = "0.1.0"
description = "Backend skeleton for lame-rms"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "lame-rms", email = "dev@example.com"},
]
dependencies = [
    "fastapi>=0.115,<0.116",
    "uvicorn[standard]>=0.30,<0.31",
    "SQLAlchemy>=2.0,<3.0",
    "psycopg[binary]>=3.1,<3.2",
    "pydantic>=2.0,<3.0",
    "pydantic-settings>=2.4,<3.0",
    "structlog>=24.1,<25.0",
    "alembic>=1.13,<1.14",
    "passlib[bcrypt]>=1.7,<1.8",
    "PyJWT>=2.9,<3.0",
    "httpx>=0.27,<0.28",
    "pytest>=8.0,<9.0",
    "pytest-cov>=4.1,<5.0",
]

[project.optional-dependencies]
lint = [
    "ruff>=0.6.0",
    "black>=24.0,<25.0",
    "mypy>=1.10,<2.0",
]

[project.urls]
Homepage = "https://example.com"

[tool.setuptools.packages.find]
where = ["app"]

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra"
testpaths = ["tests"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
ignore = []

[tool.mypy]
python_version = "3.11"
plugins = []
strict = true
warn_unused_configs = true
warn_return_any = true
warn_unused_ignores = true
show_error_codes = true
mypy_path = ["app"]
''',
}


def ensure_directories(repo_root: Path) -> None:
    directories: Iterable[str] = [
        "backend/app/core",
        "backend/app/api/routes",
        "backend/app/services",
        "backend/app/repositories",
        "backend/app/auth",
        "backend/app/integrations",
        "backend/tests/api",
        "backend/data",
    ]
    for relative in directories:
        (repo_root / relative).mkdir(parents=True, exist_ok=True)


def write_file(repo_root: Path, relative_path: str, content: str) -> None:
    destination = repo_root / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    text = textwrap.dedent(content).strip("\n") + "\n"
    destination.write_text(text, encoding="utf-8")


def remove_legacy_files(repo_root: Path) -> None:
    legacy_files = ["backend/tests/test_health.py"]
    for relative in legacy_files:
        path = repo_root / relative
        if path.exists():
            path.unlink()


def generate_backend(repo_root: Path) -> None:
    ensure_directories(repo_root)
    for relative_path, content in FASTAPI_FILES.items():
        write_file(repo_root, relative_path, content)
    remove_legacy_files(repo_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap FastAPI skeleton")
    parser.add_argument("--repo-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_backend(args.repo_root)


if __name__ == "__main__":
    main()
