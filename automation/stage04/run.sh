#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
BOOTSTRAP_SCRIPT="$SCRIPT_DIR/bootstrap_fastapi.py"
REPORT_PATH="$SCRIPT_DIR/report.md"
ENDPOINTS_MD="$SCRIPT_DIR/endpoints.md"
ENDPOINTS_JSON="$SCRIPT_DIR/endpoints.json"
STATUS_FILE="$SCRIPT_DIR/status.json"
DATA_DIR="$REPO_ROOT/backend/data"

log() {
  printf '[stage04] %s\n' "$1"
}

log "Bootstrapping FastAPI application structure"
"$PYTHON_BIN" "$BOOTSTRAP_SCRIPT" --repo-root "$REPO_ROOT"

mkdir -p "$DATA_DIR"
DB_URL="sqlite:///${DATA_DIR}/app.db"
log "Using database URL: $DB_URL"

log "Running database migrations via Alembic"
pushd "$REPO_ROOT/backend" >/dev/null
export DATABASE_URL="$DB_URL"
PYTHONPATH="$REPO_ROOT/backend" alembic upgrade head
unset DATABASE_URL
popd >/dev/null

log "Generating OpenAPI schema and endpoint catalogue"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$REPO_ROOT" "$ENDPOINTS_MD" "$ENDPOINTS_JSON"
from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app

repo_root = Path(sys.argv[1])
endpoints_md = Path(sys.argv[2])
endpoints_json = Path(sys.argv[3])
openapi_path = repo_root / "backend/openapi.json"

openapi = app.openapi()
openapi_path.write_text(json.dumps(openapi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

rows: list[dict[str, object]] = []
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = sorted({method for method in (route.methods or set()) if method not in {"HEAD", "OPTIONS"}})
        if not methods:
            continue
        rows.append(
            {
                "methods": methods,
                "path": route.path,
                "name": route.name,
                "summary": route.summary or "",
            }
        )

rows.sort(key=lambda item: (item["path"], ",".join(item["methods"])))

lines = ["| Method | Path | Name | Summary |", "|---|---|---|---|"]
for row in rows:
    lines.append(f"| {', '.join(row['methods'])} | {row['path']} | {row['name']} | {row['summary']} |")

endpoints_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
endpoints_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

RUFF_LOG=$(mktemp)
MYPY_LOG=$(mktemp)
PYTEST_LOG=$(mktemp)
trap 'rm -f "$RUFF_LOG" "$MYPY_LOG" "$PYTEST_LOG"' EXIT

log "Running ruff lint"
ruff check "$REPO_ROOT/backend" | tee "$RUFF_LOG"

log "Running mypy type checks"
mypy "$REPO_ROOT/backend" | tee "$MYPY_LOG"

log "Running API tests"
pytest "$REPO_ROOT/backend/tests/api" -q | tee "$PYTEST_LOG"

log "Composing stage report"
{
  cat <<'EOF'
# Stage 04 Report

## Summary
- Bootstrapped FastAPI core modules, services, repositories, auth, and integrations scaffolding.
- Configured structured logging, middleware, and exception handlers.
- Generated OpenAPI specification at `backend/openapi.json`.

## Linting (ruff)
```
EOF
  cat "$RUFF_LOG"
  cat <<'EOF'
```

## Type Checking (mypy)
```
EOF
  cat "$MYPY_LOG"
  cat <<'EOF'
```

## Tests (pytest backend/tests/api -q)
```
EOF
  cat "$PYTEST_LOG"
  cat <<'EOF'
```

## Endpoints
EOF
  cat "$ENDPOINTS_MD"
} >"$REPORT_PATH"

log "Updating stage status"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$STATUS_FILE" "$ENDPOINTS_JSON"
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

status_path = Path(__import__("sys").argv[1])
endpoints_json = Path(__import__("sys").argv[2])

endpoints: list[dict[str, Any]] = []
if endpoints_json.exists():
    endpoints = json.loads(endpoints_json.read_text(encoding="utf-8"))

timestamp = datetime.now(timezone.utc).isoformat()

payload = {
    "$schema": "../status.schema.json",
    "state": "completed",
    "checks": [
        {"name": "bootstrap", "status": "ok", "message": "FastAPI skeleton created"},
        {"name": "alembic-upgrade", "status": "ok", "message": "alembic upgrade head"},
        {"name": "ruff", "status": "ok", "message": "ruff check backend"},
        {"name": "mypy", "status": "ok", "message": "mypy backend"},
        {"name": "pytest", "status": "ok", "message": "pytest backend/tests/api -q"},
        {"name": "openapi", "status": "ok", "message": "backend/openapi.json generated"},
    ],
    "artifacts": [
        "backend/app/core/config.py",
        "backend/app/core/logging.py",
        "backend/app/core/middleware.py",
        "backend/app/core/exceptions.py",
        "backend/app/main.py",
        "backend/app/api/routes/health.py",
        "backend/app/services/health.py",
        "backend/tests/api/test_health.py",
        "backend/openapi.json",
        "backend/requirements.txt",
        "backend/.pre-commit-config.yaml",
        "backend/pydantic_settings/__init__.py",
        "backend/structlog/__init__.py",
        "backend/pyproject.toml",
        "automation/stage04/report.md",
        "automation/stage04/endpoints.md",
        "automation/stage04/endpoints.json",
    ],
    "last_run": timestamp,
    "warnings": [],
    "notes": ["run.sh executed"],
    "extra": {
        "api_snapshot": endpoints,
    },
}

status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Stage 04 setup complete"
