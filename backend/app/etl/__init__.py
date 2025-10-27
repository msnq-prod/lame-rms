from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from sqlalchemy.engine import Engine

from . import extract, load, transform


def run_pipeline(source: Path, engine: Engine) -> Dict[str, Any]:
    """Run the ETL pipeline and return statistics."""
    raw = extract.extract_from_json(source)
    transformed = transform.transform_raw(raw)
    return load.load_into_database(engine, transformed)
