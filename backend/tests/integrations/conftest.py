from __future__ import annotations

import os
from importlib import reload
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def configure_celery() -> Generator[None, None, None]:
    os.environ.setdefault("APP_CELERY_BROKER_URL", "memory://")
    os.environ.setdefault("APP_CELERY_RESULT_BACKEND", "cache+memory://")
    os.environ.setdefault("APP_QUEUE_FALLBACK_ENABLED", "true")
    from app import worker

    reload(worker)
    try:
        yield
    finally:
        reload(worker)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
