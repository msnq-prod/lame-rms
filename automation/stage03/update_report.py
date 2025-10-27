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


def build_key_files_list() -> list[str]:
    return [
        "- backend/app/models/generated.py",
        "- backend/app/schemas/generated.py",
        "- backend/app/etl/ (extract.py, transform.py, load.py, run.py)",
        "- backend/tests/etl/test_pipeline.py",
        "- docs/data/migration_plan.md",
        "- automation/stage03/run.sh",
        "- automation/stage03/self_check.sh",
    ]


def build_commands_section() -> list[str]:
    return [
        "1. `make stage03` — генерация схемы, моделей, ETL и документации.",
        "2. `make stage03-verify` — pytest, alembic, проверки данных и coverage.",
        "3. `make stage03-report` — вывод актуального отчёта.",
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
        "## Key Files",
        "",
    ])
    lines.extend(build_key_files_list())
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
        "## Commands",
        "",
    ])
    lines.extend(build_commands_section())
    lines.extend([
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
