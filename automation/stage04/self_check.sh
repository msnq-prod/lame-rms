#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
SELF_STATUS_FILE=${STATUS_FILE:-$SCRIPT_DIR/status.json}
TOOLS_STATUS_FILE="$SCRIPT_DIR/tools_status.json"
ENDPOINTS_JSON="$SCRIPT_DIR/endpoints.json"
OPENAPI_PATH="$REPO_ROOT/backend/openapi.json"
UVICORN_LOG="$SCRIPT_DIR/uvicorn_smoke.log"
ENSURE_LOG="$SCRIPT_DIR/ensure_tools.log"

log() {
  printf '[stage04:self-check] %s\n' "$1"
}

log "Ensuring optional tooling availability"
export STATUS_FILE="$TOOLS_STATUS_FILE"
"$REPO_ROOT/automation/bin/ensure_tools.sh" >"$ENSURE_LOG" 2>&1 || true
unset STATUS_FILE

ruff_status="fail"
log "Running ruff check"
if ruff check "$REPO_ROOT/backend"; then
  ruff_status="ok"
fi

mypy_status="fail"
log "Running mypy"
if mypy "$REPO_ROOT/backend"; then
  mypy_status="ok"
fi

pytest_status="fail"
log "Running API pytest suite"
if pytest "$REPO_ROOT/backend/tests/api" -q; then
  pytest_status="ok"
fi

openapi_status="fail"
log "Validating OpenAPI artifact"
if [[ -f "$OPENAPI_PATH" ]]; then
  openapi_status="ok"
fi

smoke_status="fail"
smoke_command="uvicorn startup/shutdown"
log "Performing uvicorn smoke test"
if PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$UVICORN_LOG" "$REPO_ROOT/backend"
import sys
from pathlib import Path

from uvicorn import Config

log_path, app_dir = sys.argv[1:3]

sys.path.insert(0, app_dir)

config = Config("app.main:app", loop="asyncio", log_level="warning")
config.load()

Path(log_path).write_text("uvicorn config load completed\n", encoding="utf-8")
PY
then
  smoke_status="ok"
else
  # ensure log exists for failure context
  if [[ ! -f "$UVICORN_LOG" ]]; then
    printf 'uvicorn smoke failed\n' >"$UVICORN_LOG"
  fi
fi

log "Recording self-check status"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' \
  "$SELF_STATUS_FILE" \
  "$ENDPOINTS_JSON" \
  "$TOOLS_STATUS_FILE" \
  "$ENSURE_LOG" \
  "$ruff_status" \
  "$mypy_status" \
  "$pytest_status" \
  "$openapi_status" \
  "$smoke_status" \
  "$smoke_command" \
  "$UVICORN_LOG"
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

(
    status_path,
    endpoints_json,
    tools_status_path,
    ensure_log_path,
    ruff_status,
    mypy_status,
    pytest_status,
    openapi_status,
    smoke_status,
    smoke_command,
    smoke_log_path,
) = sys.argv[1:]

status_file = Path(status_path)
endpoints_file = Path(endpoints_json)
tools_status_file = Path(tools_status_path)
smoke_log = Path(smoke_log_path)

existing: dict[str, Any]
if status_file.exists():
    existing = json.loads(status_file.read_text(encoding="utf-8"))
else:
    existing = {
        "$schema": "../status.schema.json",
        "state": "pending",
        "checks": [],
        "artifacts": [],
        "last_run": None,
        "warnings": [],
        "notes": [],
        "extra": {},
    }

checks: list[dict[str, Any]] = list(existing.get("checks", []))


def upsert_check(name: str, status: str, message: str) -> None:
    for check in checks:
        if check.get("name") == name:
            check.update({"status": status, "message": message})
            break
    else:
        checks.append({"name": name, "status": status, "message": message})


upsert_check("ruff", ruff_status, "ruff check backend")
upsert_check("mypy", mypy_status, "mypy backend")
upsert_check("pytest", pytest_status, "pytest backend/tests/api -q")
upsert_check("openapi-artifact", openapi_status, "backend/openapi.json present")
upsert_check("uvicorn-smoke", smoke_status, f"{smoke_command}")

warnings: list[dict[str, str]] = list(existing.get("warnings", []))
extra: dict[str, Any] = dict(existing.get("extra", {}))

if tools_status_file.exists():
    tools_payload = json.loads(tools_status_file.read_text(encoding="utf-8"))
    tools_warnings = tools_payload.get("warnings", [])
    if tools_warnings:
        warnings = tools_warnings
    tools_summary = tools_payload.get("extra", {}).get("tools_summary")
    if tools_summary:
        extra["tools_summary"] = tools_summary

api_snapshot: list[dict[str, Any]] = extra.get("api_snapshot", [])
if endpoints_file.exists():
    api_snapshot = json.loads(endpoints_file.read_text(encoding="utf-8"))
    extra["api_snapshot"] = api_snapshot

smoke_entry = {
    "command": smoke_command,
    "status": smoke_status,
    "log": str(smoke_log.relative_to(status_file.parent)) if smoke_log.exists() else None,
}
extra["smoke"] = smoke_entry

state = "completed" if all(check.get("status") == "ok" for check in checks) else "needs_attention"

payload = {
    "$schema": "../status.schema.json",
    "state": state,
    "checks": checks,
    "artifacts": existing.get("artifacts", []),
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": existing.get("notes", []),
    "extra": extra,
}

status_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Self-check complete"
