from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text


def test_run_cli_creates_tables_and_loads(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    database_url = f"sqlite+pysqlite:///{tmp_path / 'etl.sqlite'}"

    env = os.environ.copy()
    pythonpath = [str(repo_root / "backend")]
    if existing := env.get("PYTHONPATH"):
        pythonpath.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath)

    result = subprocess.run(
        [sys.executable, "-m", "app.etl.run", "--database-url", database_url],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Loaded 3 rows across 2 tables" in result.stdout

    engine = create_engine(database_url, future=True)
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {"actions", "actionsCategories"}.issubset(tables)

        with engine.connect() as connection:
            actions = connection.execute(text('SELECT COUNT(*) FROM "actions"')).scalar_one()
            categories = connection.execute(text('SELECT COUNT(*) FROM "actionsCategories"')).scalar_one()

        assert actions == 2
        assert categories == 1
    finally:
        engine.dispose()
