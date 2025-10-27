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
