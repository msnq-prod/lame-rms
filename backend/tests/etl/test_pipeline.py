from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

from app.db.base import Base
import app.models  # noqa: F401
from app.etl import run_pipeline

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_dump.json"


def create_sqlite_engine():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
    return engine


def test_pipeline_loads_rows():
    engine = create_sqlite_engine()
    Base.metadata.create_all(engine)
    stats = run_pipeline(FIXTURE_PATH, engine)
    assert stats["tables"]["actions"] == 2
    assert stats["tables"]["actionsCategories"] == 1
    with engine.connect() as conn:
        total_actions = conn.execute(text('SELECT COUNT(*) FROM "actions"')).scalar_one()
        total_categories = conn.execute(text('SELECT COUNT(*) FROM "actionsCategories"')).scalar_one()
    assert total_actions == 2
    assert total_categories == 1
