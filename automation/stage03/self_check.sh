#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
STATUS_FILE=${STATUS_FILE:-$SCRIPT_DIR/status.json}
STAGE_STATUS_FILE="$STATUS_FILE"
TOOLS_STATUS_FILE="$SCRIPT_DIR/tools_status.json"
RESULTS_FILE="$SCRIPT_DIR/self_check_results.json"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
COVERAGE_RAW="$SCRIPT_DIR/.coverage_raw.json"
COVERAGE_JSON="$SCRIPT_DIR/coverage.json"
ETL_RESULTS="$SCRIPT_DIR/etl_results.json"
PYTEST_LOG="$SCRIPT_DIR/pytest.log"
ALEMBIC_LOG="$SCRIPT_DIR/alembic.log"
ENSURE_LOG="$SCRIPT_DIR/ensure_tools.log"

export PYTHONPATH="$REPO_ROOT/backend"

: >"$ALEMBIC_LOG"
: >"$PYTEST_LOG"
: >"$ENSURE_LOG"

log() {
  printf '[stage03:self-check] %s\n' "$1"
}

log "Ensuring optional tooling availability"
export STATUS_FILE="$TOOLS_STATUS_FILE"
"$REPO_ROOT/automation/bin/ensure_tools.sh" >"$ENSURE_LOG" 2>&1 || true
unset STATUS_FILE
STATUS_FILE="$STAGE_STATUS_FILE"

pytest_status="fail"
pytest_details="pytest did not run"
log "Running pytest suite for ETL"
if pushd "$REPO_ROOT/backend" >/dev/null; then
  if "$PYTHON_BIN" -m pytest tests/etl -q --cov=app.etl --cov-report=json:"$COVERAGE_RAW" >"$PYTEST_LOG" 2>&1; then
    pytest_status="pass"
    pytest_details="backend/tests/etl (see pytest.log)"
  else
    pytest_status="fail"
    pytest_details="Tests failed (see pytest.log)"
  fi
  popd >/dev/null || true
else
  pytest_status="fail"
  pytest_details="Cannot access backend directory"
fi

alembic_status="warn"
alembic_details="docker not available"
compose_cmd=""
if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    compose_cmd="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    compose_cmd="docker-compose"
  fi
fi

if [[ -n "$compose_cmd" ]]; then
  log "Starting postgres-test container for Alembic checks"
  if $compose_cmd -f "$REPO_ROOT/docker-compose.yml" up -d postgres-test >"$ALEMBIC_LOG" 2>&1; then
    log "Waiting for postgres-test service"
    if "$PYTHON_BIN" - <<'PY' >>"$ALEMBIC_LOG" 2>&1 5532
import socket
import sys
import time

PORT = int(sys.argv[1])
HOST = "127.0.0.1"
DEADLINE = time.time() + 60
while time.time() < DEADLINE:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        try:
            sock.connect((HOST, PORT))
        except OSError:
            time.sleep(2)
        else:
            print("postgres-test reachable")
            break
else:
    print("postgres-test did not become reachable", file=sys.stderr)
    sys.exit(1)
PY
    then
      log "Running Alembic upgrade head"
      if pushd "$REPO_ROOT/backend" >/dev/null; then
        if DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5532/postgres" "$PYTHON_BIN" -m alembic upgrade head >>"$ALEMBIC_LOG" 2>&1; then
          alembic_status="pass"
          alembic_details="alembic upgrade head"
        else
          alembic_status="fail"
          alembic_details="alembic upgrade head failed (see alembic.log)"
        fi
        popd >/dev/null || true
      else
        alembic_status="fail"
        alembic_details="Cannot access backend directory"
      fi
    else
      alembic_status="fail"
      alembic_details="postgres-test not reachable (see alembic.log)"
    fi
    log "Stopping postgres-test container"
    $compose_cmd -f "$REPO_ROOT/docker-compose.yml" rm -sf postgres-test >>"$ALEMBIC_LOG" 2>&1 || true
  else
    alembic_status="fail"
    alembic_details="Failed to start postgres-test (see alembic.log)"
  fi
else
  log "Docker not available; falling back to temporary PostgreSQL"
  temp_dir=$(mktemp -d)
  temp_uri_file="$temp_dir/pg_tmp_uri"
  pg_tmp_pid=""
  cleanup_pg_tmp() {
    if [[ -n "$pg_tmp_pid" ]] && kill -0 "$pg_tmp_pid" >/dev/null 2>&1; then
      kill "$pg_tmp_pid" >/dev/null 2>&1 || true
      wait "$pg_tmp_pid" >/dev/null 2>&1 || true
    fi
    rm -rf "$temp_dir"
  }
  trap cleanup_pg_tmp EXIT
  if "$PYTHON_BIN" "$REPO_ROOT/automation/bin/run_pg_tmp.py" >"$temp_uri_file" 2>>"$ALEMBIC_LOG" & then
    pg_tmp_pid=$!
    temp_database_url=""
    for _ in $(seq 1 30); do
      if [[ -s "$temp_uri_file" ]]; then
        temp_database_url=$(head -n1 "$temp_uri_file")
        break
      fi
      if ! kill -0 "$pg_tmp_pid" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    if [[ -n "$temp_database_url" ]]; then
      printf 'Temporary PostgreSQL URI: %s\n' "$temp_database_url" >>"$ALEMBIC_LOG"
      if pushd "$REPO_ROOT/backend" >/dev/null; then
        if DATABASE_URL="$temp_database_url" "$PYTHON_BIN" -m alembic upgrade head >>"$ALEMBIC_LOG" 2>&1; then
          alembic_status="pass"
          alembic_details="alembic upgrade head (pg_tmp)"
        else
          alembic_status="fail"
          alembic_details="alembic upgrade head failed (pg_tmp, see alembic.log)"
        fi
        popd >/dev/null || true
      else
        alembic_status="fail"
        alembic_details="Cannot access backend directory"
      fi
    else
      alembic_status="fail"
      alembic_details="Temporary PostgreSQL did not provide URI (see alembic.log)"
    fi
  else
    alembic_status="fail"
    alembic_details="Failed to launch run_pg_tmp.py (see alembic.log)"
  fi
  cleanup_pg_tmp
  trap - EXIT
fi

log "Running ETL validation checks"
"$PYTHON_BIN" - <<'PY' "$REPO_ROOT" "$ETL_RESULTS"
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine

from app.db.base import Base
import app.models  # noqa: F401
from app.etl import run_pipeline

repo_root = Path(sys.argv[1])
output_path = Path(sys.argv[2])
fixture = repo_root / "backend" / "tests" / "etl" / "fixtures" / "sample_dump.json"
engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
with engine.begin() as conn:
    conn.exec_driver_sql("PRAGMA foreign_keys=ON")
Base.metadata.create_all(engine)
stats = run_pipeline(fixture, engine)
row_counts = {}
with engine.connect() as conn:
    for table in stats.get("tables", {}):
        count = conn.exec_driver_sql(f'SELECT COUNT(*) FROM "{table}"').scalar_one()
        row_counts[table] = int(count)
    fk_errors = conn.exec_driver_sql("PRAGMA foreign_key_check").all()

payload = {
    "stats": stats,
    "row_counts": row_counts,
    "foreign_key_errors": [list(row) for row in fk_errors],
}
output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

log "Aggregating self-check results"
"$PYTHON_BIN" - <<'PY' \
  "$STATUS_FILE" \
  "$RESULTS_FILE" \
  "$TOOLS_STATUS_FILE" \
  "$SUMMARY_JSON" \
  "$COVERAGE_RAW" \
  "$COVERAGE_JSON" \
  "$ETL_RESULTS" \
  "$pytest_status" \
  "$pytest_details" \
  "$alembic_status" \
  "$alembic_details"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
results_path = Path(sys.argv[2])
tools_status_path = Path(sys.argv[3])
summary_path = Path(sys.argv[4])
coverage_raw_path = Path(sys.argv[5])
coverage_path = Path(sys.argv[6])
etl_results_path = Path(sys.argv[7])
pytest_status = sys.argv[8]
pytest_details = sys.argv[9]
alembic_status = sys.argv[10]
alembic_details = sys.argv[11]

summary = {}
if summary_path.exists():
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

tools_status = {}
if tools_status_path.exists():
    tools_status = json.loads(tools_status_path.read_text(encoding="utf-8"))

etl_results = {}
if etl_results_path.exists():
    etl_results = json.loads(etl_results_path.read_text(encoding="utf-8"))

coverage_summary = {}
modules = {}
if coverage_raw_path.exists():
    raw = json.loads(coverage_raw_path.read_text(encoding="utf-8"))
    totals = raw.get("totals", {})
    files = raw.get("files", {})
    for path, info in files.items():
        summary_info = info.get("summary", {})
        modules[Path(path).name] = {
            "covered_lines": summary_info.get("covered_lines", 0),
            "total_lines": summary_info.get("num_statements", 0),
        }
    coverage_summary = {
        "covered_lines": totals.get("covered_lines", 0),
        "total_lines": totals.get("num_statements", 0),
        "percent": round(totals.get("percent_covered", 0.0), 2),
        "modules": modules,
    }
    coverage_path.write_text(json.dumps(coverage_summary, indent=2), encoding="utf-8")

run_py_status = "fail"
run_py_details = "Coverage summary unavailable"
if coverage_summary:
    run_module = modules.get("run.py")
    if run_module is None:
        run_py_details = "run.py missing from coverage report"
    else:
        covered = run_module.get("covered_lines", 0)
        total = run_module.get("total_lines", 0)
        run_py_details = f"run.py covered_lines={covered}/{total}"
        run_py_status = "pass" if covered > 0 else "fail"

tool_checks = tools_status.get("checks", [])
if tool_checks:
    tool_details = ", ".join(f"{item['name']}={item['status']}" for item in tool_checks)
    tooling_status = "pass" if all(item.get("status") in {"ok", "installed"} for item in tool_checks) else "warn"
else:
    tool_details = "Tooling status unavailable"
    tooling_status = "warn"

tool_warnings = [
    f"{entry.get('tool')}: {entry.get('message')}"
    for entry in tools_status.get("warnings", [])
]

row_checks = etl_results.get("stats", {}).get("tables", {})
row_counts = etl_results.get("row_counts", {})
row_status = "pass"
row_detail_parts = []
for table, expected in row_checks.items():
    actual = row_counts.get(table)
    row_detail_parts.append(f"{table}={actual}/{expected}")
    if actual != expected:
        row_status = "fail"
row_details = ", ".join(row_detail_parts) if row_detail_parts else "No tables processed"

fk_errors = etl_results.get("foreign_key_errors", [])
fk_status = "pass" if not fk_errors else "fail"
fk_details = "No foreign key violations" if not fk_errors else f"Violations: {len(fk_errors)}"

checks = {
    "tooling": {
        "label": "Tooling",
        "status": "pass" if tooling_status == "pass" else "warn",
        "details": tool_details,
    },
    "pytest": {
        "label": "Pytest (ETL)",
        "status": "pass" if pytest_status == "pass" else "fail",
        "details": pytest_details,
    },
    "alembic": {
        "label": "Alembic upgrade",
        "status": "pass" if alembic_status == "pass" else ("warn" if alembic_status == "warn" else "fail"),
        "details": alembic_details,
    },
    "rows": {
        "label": "Row counts",
        "status": "pass" if row_status == "pass" else "fail",
        "details": row_details,
    },
    "foreign_keys": {
        "label": "Foreign keys",
        "status": "pass" if fk_status == "pass" else "fail",
        "details": fk_details,
    },
    "run_py_coverage": {
        "label": "run.py coverage",
        "status": "pass" if run_py_status == "pass" else "fail",
        "details": run_py_details,
    },
}

warnings = []
warnings.extend(tool_warnings)
if alembic_status != "pass":
    warnings.append(alembic_details)
if run_py_status != "pass":
    warnings.append(run_py_details)

results_payload = {
    "checks": checks,
    "warnings": warnings,
    "coverage": coverage_summary,
    "etl_stats": etl_results.get("stats", {}),
}

results_path.write_text(json.dumps(results_payload, indent=2), encoding="utf-8")

status_checks = []
state = "completed"
for key, value in checks.items():
    result = value["status"]
    mapped = "ok"
    if result == "fail":
        mapped = "fail"
        state = "needs_attention"
    elif result == "warn":
        mapped = "warning"
        if state != "needs_attention":
            state = "needs_attention"
    status_checks.append({
        "name": key,
        "status": mapped,
        "message": value["details"],
    })

artifacts = [
    "automation/stage03/report.md",
    "automation/stage03/coverage.json",
    "automation/stage03/self_check_results.json",
    "automation/stage03/etl_results.json",
    "automation/stage03/pytest.log",
    "automation/stage03/alembic.log",
    "automation/stage03/ensure_tools.log",
]

extra = {
    "coverage": coverage_summary,
    "etl_stats": etl_results.get("stats", {}),
}
if summary:
    extra["summary"] = summary

payload = {
    "$schema": "../status.schema.json",
    "state": state,
    "checks": status_checks,
    "artifacts": artifacts,
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": ["self_check.sh executed"],
    "extra": extra,
}

status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

rm -f "$COVERAGE_RAW" || true

log "Updating stage report"
"$PYTHON_BIN" "$SCRIPT_DIR/update_report.py" --summary "$SUMMARY_JSON" --results "$RESULTS_FILE" --output "$SCRIPT_DIR/report.md"

log "Stage 03 self-check complete"
