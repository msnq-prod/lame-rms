#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
STATUS_FILE_PATH="${STATUS_FILE:-$SCRIPT_DIR/status.json}"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
RESULTS_JSON="$SCRIPT_DIR/self_check_results.json"
COVERAGE_JSON="$SCRIPT_DIR/coverage.json"
TRACE_DIR="$SCRIPT_DIR/tracecov"
ETL_JSON="$SCRIPT_DIR/etl_results.json"
TOOLS_JSON="$SCRIPT_DIR/tools_status.json"
PYTEST_LOG="$SCRIPT_DIR/pytest.log"
ALEMBIC_LOG="$SCRIPT_DIR/alembic.log"
SCHEMA_JSON="$SCRIPT_DIR/schema.json"

CHECKS_FILE=$(mktemp)
WARNINGS_FILE=$(mktemp)
FAILED=0
POSTGRES_STARTED=0
COMPOSE_CMD=""

cleanup() {
  if [[ "$POSTGRES_STARTED" -eq 1 && -n "$COMPOSE_CMD" ]]; then
    $COMPOSE_CMD stop postgres-test >/dev/null 2>&1 || true
    $COMPOSE_CMD rm -f postgres-test >/dev/null 2>&1 || true
  fi
  rm -f "$CHECKS_FILE" "$WARNINGS_FILE"
}

trap cleanup EXIT

record_check() {
  local key="$1"
  local label="$2"
  local status="$3"
  local details="$4"
  printf '%s\t%s\t%s\t%s\n' "$key" "$label" "$status" "$details" >>"$CHECKS_FILE"
  if [[ "$status" == "fail" ]]; then
    FAILED=1
  fi
}

add_warning() {
  printf '%s\n' "$1" >>"$WARNINGS_FILE"
}

# Tooling availability
STATUS_FILE="$TOOLS_JSON" "$REPO_ROOT/automation/bin/ensure_tools.sh"

tool_summary=$(python3 - "$TOOLS_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)
rows = payload.get("tools", [])
warnings = [row for row in rows if row.get("status") not in {"ok", "installed"}]
status = "pass" if not warnings else "warn"
details = ", ".join(f"{row['name']}={row['status']}" for row in rows) or "no tools checked"
print(status)
print(details)
PY
)

tool_status=$(printf '%s\n' "$tool_summary" | head -n1)
tool_details=$(printf '%s\n' "$tool_summary" | tail -n +2 | paste -sd ' ' -)
record_check "tooling" "Tooling" "$tool_status" "$tool_details"
if [[ "$tool_status" == "warn" ]]; then
  add_warning "Some optional tools are unavailable: $tool_details"
fi

# Run pytest under trace to gather coverage
rm -rf "$TRACE_DIR"
mkdir -p "$TRACE_DIR"
set +e
PYTHONPATH="$REPO_ROOT/backend" python -m trace --count --coverdir="$TRACE_DIR" --module pytest "$REPO_ROOT/backend/tests/etl" -q >"$PYTEST_LOG" 2>&1
pytest_exit=$?
set -e
if [[ $pytest_exit -eq 0 ]]; then
  record_check "pytest" "Pytest (ETL)" "pass" "backend/tests/etl"
else
  record_check "pytest" "Pytest (ETL)" "fail" "See pytest.log"
fi

# Determine docker compose availability
if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
  else
    record_check "alembic" "Alembic upgrade" "warn" "docker compose not available"
    add_warning "docker compose plugin missing"
  fi
else
  record_check "alembic" "Alembic upgrade" "warn" "docker not available"
  add_warning "Cannot start postgres-test: docker missing"
fi

rm -f "$ETL_JSON"

run_etl_python() {
  local db_url="$1"
  python3 - "$REPO_ROOT" "$ETL_JSON" "$SCHEMA_JSON" "$db_url" <<'PY'
import json
import sys
from pathlib import Path

repo_root = Path(sys.argv[1])
output_path = Path(sys.argv[2])
schema_path = Path(sys.argv[3])
db_url = sys.argv[4]

sys.path.insert(0, str(repo_root / "backend"))

import app.models  # noqa: F401
from sqlalchemy import create_engine, text
from app.db.base import Base
from app.etl import run_pipeline

fixture = repo_root / "backend" / "tests" / "etl" / "fixtures" / "sample_dump.json"
if db_url:
    engine = create_engine(db_url, future=True)
else:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
Base.metadata.create_all(engine)
stats = run_pipeline(fixture, engine)
with open(schema_path, "r", encoding="utf-8") as handle:
    schema = json.load(handle)
foreign_failures = 0
row_counts: dict[str, int] = {}
with engine.connect() as conn:
    for table, expected in stats.get("tables", {}).items():
        quoted_table = f'"{table}"'
        row_counts[table] = conn.execute(text(f"SELECT COUNT(*) FROM {quoted_table}")).scalar_one()
        table_schema = schema.get("tables", {}).get(table, {})
        for fk in (table_schema.get("foreign_keys") or {}).values():
            column = fk["COLUMN_NAME"]
            ref_table = fk["REFERENCED_TABLE_NAME"]
            ref_column = fk["REFERENCED_COLUMN_NAME"]
            check_sql = text(
                f'SELECT COUNT(*) FROM "{table}" AS t '
                f'LEFT JOIN "{ref_table}" AS r '
                f'ON t."{column}" = r."{ref_column}" '
                f'WHERE t."{column}" IS NOT NULL AND r."{ref_column}" IS NULL'
            )
            foreign_failures += conn.execute(check_sql).scalar_one()
result = {
    "etl_stats": stats,
    "row_counts": row_counts,
    "foreign_failures": foreign_failures,
}
with open(output_path, "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
PY
}

if [[ -n "$COMPOSE_CMD" ]]; then
  POSTGRES_USER="${POSTGRES_USER:-postgres}"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
  POSTGRES_DB="${POSTGRES_DB:-postgres}"
  export POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB
  $COMPOSE_CMD up -d postgres-test >/dev/null 2>&1 && POSTGRES_STARTED=1
  if [[ "$POSTGRES_STARTED" -eq 1 ]]; then
    READY=0
    for _ in {1..15}; do
      if $COMPOSE_CMD exec -T postgres-test pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        READY=1
        break
      fi
      sleep 2
    done
    if [[ $READY -eq 1 ]]; then
      DATABASE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5532/$POSTGRES_DB"
      set +e
      (cd "$REPO_ROOT/backend" && DATABASE_URL="$DATABASE_URL" alembic upgrade head >"$ALEMBIC_LOG" 2>&1)
      alembic_status=$?
      set -e
      if [[ $alembic_status -eq 0 ]]; then
        record_check "alembic" "Alembic upgrade" "pass" "alembic upgrade head"
        run_etl_python "$DATABASE_URL"
      else
        record_check "alembic" "Alembic upgrade" "fail" "See alembic.log"
      fi
    else
      record_check "alembic" "Alembic upgrade" "fail" "postgres-test not ready"
      add_warning "postgres-test service failed health check"
    fi
  fi
elif [[ $pytest_exit -eq 0 ]]; then
  run_etl_python ""
fi

if [[ -f "$ETL_JSON" ]]; then
  row_check=$(python3 - "$ETL_JSON" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
row_counts = data.get("row_counts", {})
stats = data.get("etl_stats", {}).get("tables", {})
row_mismatches = [
    f"{table}: inserted {row_counts.get(table)} != expected {expected}"
    for table, expected in stats.items()
    if row_counts.get(table) != expected
]
foreign_failures = data.get("foreign_failures", 0)
if row_mismatches:
    print("fail")
    print("; ".join(row_mismatches))
else:
    print("pass")
    total_rows = sum(row_counts.values())
    print(f"{total_rows} rows loaded across {len(row_counts)} tables")
print(foreign_failures)
PY
)
  row_status=$(printf '%s\n' "$row_check" | head -n1)
  row_details=$(printf '%s\n' "$row_check" | head -n2 | tail -n1)
  fk_failures=$(printf '%s\n' "$row_check" | tail -n1)
  record_check "rows" "Row counts" "$row_status" "$row_details"
  if [[ "$fk_failures" -eq 0 ]]; then
    record_check "foreign_keys" "Foreign keys" "pass" "No missing references"
  else
    record_check "foreign_keys" "Foreign keys" "fail" "$fk_failures orphaned rows"
  fi
else
  record_check "rows" "Row counts" "warn" "ETL results missing"
  record_check "foreign_keys" "Foreign keys" "warn" "ETL results missing"
fi

# Compute coverage summary
python3 - "$TRACE_DIR" "$REPO_ROOT/backend/app/etl" "$COVERAGE_JSON" <<'PY'
import json
import sys
from pathlib import Path

trace_dir = Path(sys.argv[1])
source_dir = Path(sys.argv[2])
output_path = Path(sys.argv[3])

total_lines = 0
covered_lines = 0
modules = {}
for cover_file in trace_dir.glob("app.etl.*.cover"):
    parts = cover_file.stem.split(".")
    if parts[:2] != ["app", "etl"]:
        continue
    module_total = 0
    module_covered = 0
    with cover_file.open("r", encoding="utf-8") as handle:
        for raw in handle:
            if ":" not in raw:
                continue
            count_str, code = raw.split(":", 1)
            stripped = code.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("\"\"\"") or stripped.startswith("'''"):
                continue
            module_total += 1
            try:
                count = int(count_str.strip())
            except ValueError:
                count = 0
            if count > 0:
                module_covered += 1
    total_lines += module_total
    covered_lines += module_covered
    modules[f"{parts[2]}.py"] = {
        "covered_lines": module_covered,
        "total_lines": module_total,
    }
percent = round((covered_lines / total_lines) * 100, 2) if total_lines else 0.0
with output_path.open("w", encoding="utf-8") as handle:
    json.dump(
        {
            "covered_lines": covered_lines,
            "total_lines": total_lines,
            "percent": percent,
            "modules": modules,
        },
        handle,
    )
PY

python3 - "$SUMMARY_JSON" "$RESULTS_JSON" "$CHECKS_FILE" "$WARNINGS_FILE" "$STATUS_FILE_PATH" "$TOOLS_JSON" "$COVERAGE_JSON" "$ETL_JSON" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

summary_path, results_path, checks_file, warnings_file, status_path, tools_path, coverage_path, etl_path = sys.argv[1:9]

checks = {}
with open(checks_file, "r", encoding="utf-8") as handle:
    for line in handle:
        key, label, status, details = line.rstrip("\n").split("\t")
        checks[key] = {"label": label, "status": status, "details": details}

warnings = []
with open(warnings_file, "r", encoding="utf-8") as handle:
    warnings = [line.strip() for line in handle if line.strip()]

coverage = {}
if Path(coverage_path).exists():
    with open(coverage_path, "r", encoding="utf-8") as handle:
        coverage = json.load(handle)

etl_stats = {}
if Path(etl_path).exists():
    with open(etl_path, "r", encoding="utf-8") as handle:
        etl_stats = json.load(handle)

results_payload = {
    "checks": checks,
    "warnings": warnings,
    "coverage": coverage,
    "etl_stats": etl_stats.get("etl_stats", {}),
}
with open(results_path, "w", encoding="utf-8") as handle:
    json.dump(results_payload, handle, indent=2)

state = "ready" if all(entry["status"] != "fail" for entry in checks.values()) else "needs-attention"

artifacts = [
    {"type": "diagram", "path": "docs/data/er_diagram.mmd", "description": "ER diagram"},
    {"type": "schema", "path": "automation/stage03/schema.json", "description": "Legacy schema snapshot"},
    {"type": "models", "path": "backend/app/models/generated.py", "description": "SQLAlchemy models"},
    {"type": "schemas", "path": "backend/app/schemas/generated.py", "description": "Pydantic schemas"},
    {"type": "etl", "path": "backend/app/etl", "description": "ETL pipeline"},
    {"type": "report", "path": "automation/stage03/report.md", "description": "Stage report"},
]

status_payload = {
    "state": state,
    "checks": {key: {"status": value["status"], "details": value["details"]} for key, value in checks.items()},
    "artifacts": artifacts,
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": [],
    "extra": {
        "coverage": coverage,
        "etl_stats": etl_stats,
    },
}
with open(status_path, "w", encoding="utf-8") as handle:
    json.dump(status_payload, handle, indent=2)
PY

python3 "$SCRIPT_DIR/update_report.py" --summary "$SUMMARY_JSON" --results "$RESULTS_JSON"

if [[ $FAILED -eq 1 ]]; then
  exit 1
fi
