import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["Base", "engine", "SessionLocal", "get_db"]
