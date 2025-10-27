#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
GENERATOR="$SCRIPT_DIR/generate_assets.py"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
STATUS_FILE="$SCRIPT_DIR/status.json"

log() {
  printf '[stage03] %s\n' "$1"
}

if [[ ! -x "$GENERATOR" ]]; then
  chmod +x "$GENERATOR"
fi

log "Generating database migration assets"
"$PYTHON_BIN" "$GENERATOR"

log "Recording stage status"
"$PYTHON_BIN" - <<'PY' "$STATUS_FILE" "$SUMMARY_JSON"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
summary = {}
if summary_path.exists():
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

timestamp = datetime.now(timezone.utc).isoformat()

checks = [
    {
        "name": "generate-assets",
        "status": "ok",
        "message": "Schema extracted, ER diagram and models generated",
    }
]

artifacts = [
    "automation/stage03/schema.json",
    "automation/stage03/report.md",
    "automation/stage03/summary.json",
    "docs/data/er_diagram.mmd",
    "docs/data/migration_plan.md",
    "backend/app/models/generated.py",
    "backend/app/schemas/generated.py",
    "backend/app/etl/__init__.py",
    "backend/app/etl/extract.py",
    "backend/app/etl/transform.py",
    "backend/app/etl/load.py",
    "backend/app/etl/run.py",
    "backend/tests/etl/test_pipeline.py",
    "backend/tests/etl/fixtures/sample_dump.json",
]

payload = {
    "$schema": "../status.schema.json",
    "state": "prepared",
    "checks": checks,
    "artifacts": artifacts,
    "last_run": timestamp,
    "warnings": [],
    "notes": ["run.sh executed"],
    "extra": {
        "summary": summary,
    },
}

status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

log "Stage 03 asset generation complete"
