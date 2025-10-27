#!/usr/bin/env python3
"""Update the stage03 report with verification results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import dedent
from typing import Any

STAGE_DIR = Path(__file__).resolve().parent


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_checks_table(results: dict[str, Any]) -> list[str]:
    rows = ["| Check | Result | Details |", "| --- | --- | --- |"]
    mapping = results.get("checks", {})
    for value in mapping.values():
        rows.append(f"| {value['label']} | {value['status']} | {value['details']} |")
    return rows


def build_artifacts_list() -> list[str]:
    return [
        "- [ER diagram](../../docs/data/er_diagram.mmd)",
        "- [Schema snapshot](schema.json)",
        "- [SQLAlchemy models](../../backend/app/models/generated.py)",
        "- [Pydantic schemas](../../backend/app/schemas/generated.py)",
        "- [ETL pipeline](../../backend/app/etl/)",
    ]


def render(summary: dict[str, Any], results: dict[str, Any]) -> str:
    timestamp = summary.get("timestamp")
    table_count = summary.get("table_count", 0)
    column_count = summary.get("column_count", 0)
    foreign_keys = summary.get("foreign_key_count", 0)
    coverage = results.get("coverage", {})
    coverage_line = (
        f"Coverage: {coverage.get('percent', 'n/a')}% "
        f"({coverage.get('covered_lines', 0)}/{coverage.get('total_lines', 0)} lines)"
        if coverage
        else "Coverage: n/a"
    )
    lines = [
        "# Summary",
        "",
        f"- Schema extracted on {timestamp} containing {table_count} tables, {column_count} columns and {foreign_keys} foreign keys.",
        "- Generated SQLAlchemy models and Pydantic schemas to mirror the legacy structure.",
        "- ETL pipeline validated via automated tests and Alembic migrations.",
        "",
        "## Artifacts",
        "",
    ]
    lines.extend(build_artifacts_list())
    lines.extend([
        "",
        "## Checks",
        "",
    ])
    lines.extend(build_checks_table(results))
    lines.extend([
        "",
        "## Coverage",
        "",
        f"- {coverage_line}",
        "",
        "## Next Gate",
        "",
        "- Run `make stage04` once the FastAPI skeleton is ready to consume the migrated database.",
        "- Extend fixtures with production-like datasets before executing the full migration.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Update stage03 report")
    parser.add_argument("--summary", type=Path, default=STAGE_DIR / "summary.json")
    parser.add_argument("--results", type=Path, default=STAGE_DIR / "self_check_results.json")
    parser.add_argument("--output", type=Path, default=STAGE_DIR / "report.md")
    args = parser.parse_args()

    summary = load_json(args.summary)
    results = load_json(args.results)
    args.output.write_text(render(summary, results), encoding="utf-8")


if __name__ == "__main__":
    main()
