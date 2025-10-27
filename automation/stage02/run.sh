#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
GENERATOR="$SCRIPT_DIR/generate_inventory.py"
INVENTORY_DIR="$REPO_ROOT/docs/inventory"
BACKLOG_DIR="$REPO_ROOT/docs/backlog"
REPORT_PATH="$SCRIPT_DIR/report.md"
STATUS_FILE="$SCRIPT_DIR/status.json"

log() {
  printf '[stage02] %s\n' "$1"
}

if [[ ! -x "$GENERATOR" ]]; then
  log "Making generator executable"
  chmod +x "$GENERATOR"
fi

log "Preparing documentation directories"
mkdir -p "$INVENTORY_DIR" "$INVENTORY_DIR/api" "$BACKLOG_DIR"

log "Running inventory generator"
"$PYTHON_BIN" "$GENERATOR" \
  --repo-root "$REPO_ROOT" \
  --inventory-dir "$INVENTORY_DIR" \
  --backlog-dir "$BACKLOG_DIR" \
  --report-path "$REPORT_PATH"

log "Recording baseline status"
"$PYTHON_BIN" - "$STATUS_FILE" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
timestamp = datetime.now(timezone.utc).isoformat()

artifacts = [
    "docs/inventory/files.json",
    "docs/inventory/files.csv",
    "docs/inventory/files.md",
    "docs/inventory/metrics.md",
    "docs/inventory/cron.md",
    "docs/inventory/structure.mmd",
    "docs/inventory/api_surface.mmd",
    "docs/inventory/api/openapi.json",
    "docs/inventory/api/endpoints.csv",
    "docs/inventory/api/summary.md",
    "docs/backlog/migration_backlog.yaml",
    "docs/backlog/migration_backlog.json",
    "automation/stage02/report.md",
]

payload = {
    "$schema": "../status.schema.json",
    "state": "completed",
    "checks": [
        {
            "name": "generate-inventory",
            "status": "ok",
            "message": "automation/stage02/generate_inventory.py executed",
        }
    ],
    "artifacts": artifacts,
    "last_run": timestamp,
    "warnings": [],
    "notes": ["run.sh executed"],
    "extra": {},
}

status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Stage 02 inventory generation complete"
