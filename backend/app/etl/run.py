from __future__ import annotations

import argparse
import os
from pathlib import Path

from sqlalchemy import create_engine

from app.db.base import Base
import app.models  # noqa: F401
from . import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the stage03 ETL pipeline.")
    parser.add_argument("--input", type=Path, default=Path("backend/tests/etl/fixtures/sample_dump.json"), help="Path to JSON dump")
    parser.add_argument("--database-url", dest="database_url", default=os.environ.get("DATABASE_URL", "sqlite+pysqlite:///:memory:"))
    args = parser.parse_args()

    engine = create_engine(args.database_url, future=True)
    Base.metadata.create_all(engine)
    stats = run_pipeline(args.input, engine)
    print(f"Loaded {stats['total_rows']} rows across {len(stats['tables'])} tables")


if __name__ == "__main__":
    main()
