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
