from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import MODEL_REGISTRY
from sqlalchemy import text


def load_into_database(engine: Engine, transformed: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Load validated rows into the target database."""
    stats: Dict[str, Any] = {"tables": {}, "total_rows": 0}
    if engine.dialect.name == "sqlite":
        with engine.begin() as connection:
            connection.execute(text("PRAGMA foreign_keys=ON"))
    with Session(engine) as session:
        for table, rows in transformed.items():
            model = MODEL_REGISTRY.get(table)
            if model is None or not rows:
                continue
            for row in rows:
                session.merge(model(**row))
            session.flush()
            stats["tables"][table] = len(rows)
            stats["total_rows"] += len(rows)
        session.commit()
    return stats
