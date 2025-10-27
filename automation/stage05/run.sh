#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
GENERATOR="$SCRIPT_DIR/generate_from_backlog.py"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
REPORT_MD="$SCRIPT_DIR/report.md"
STATUS_JSON="$SCRIPT_DIR/status.json"
METRICS_JSON="$SCRIPT_DIR/metrics.json"
OPENAPI_PATH="$REPO_ROOT/backend/openapi.json"

log() {
  printf '[stage05] %s\n' "$1"
}

log "Syncing FastAPI domain with backlog"
"$PYTHON_BIN" "$GENERATOR"

log "Regenerating OpenAPI schema"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$OPENAPI_PATH"
import json
import sys
from pathlib import Path

from fastapi.routing import APIRoute

from app.main import app

output = Path(sys.argv[1])
openapi = app.openapi()
output.write_text(json.dumps(openapi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Composing stage report"
"$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$REPORT_MD" "$METRICS_JSON"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

summary_path = Path(sys.argv[1])
report_path = Path(sys.argv[2])
metrics_path = Path(sys.argv[3])

summary = json.loads(summary_path.read_text(encoding="utf-8"))
endpoints = summary.get("endpoints", [])
feature_flag = summary.get("feature_flag", "assets_api")
backlog = summary.get("backlog_item", {})
documentation = summary.get("documentation")

metrics_excerpt = "Load tests not yet executed. Run `make stage05-verify` to populate metrics."
if metrics_path.exists():
    try:
        metrics_data = json.loads(metrics_path.read_text(encoding="utf-8"))
        metrics_excerpt = json.dumps(metrics_data, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        metrics_excerpt = metrics_path.read_text(encoding="utf-8")

def format_endpoint(item: dict[str, str]) -> str:
    method = item.get("method", "GET")
    path = f"/api{item.get('path', '')}"
    summary = item.get("summary", "")
    operation_id = item.get("operation_id", "")
    return f"| {method} | {path} | {summary} | {operation_id} |"

lines = [
    "# Stage 05 Report",
    "",
    "## Summary",
    f"- Generated FastAPI assets domain from backlog item {backlog.get('id')}.",
    f"- Feature flag: `{feature_flag}`.",
]
if documentation:
    lines.append(f"- Documentation: `{documentation}`.")
lines.extend(
    [
        "",
        "## Endpoints",
        "",
        "| Method | Path | Summary | Operation ID |",
        "|---|---|---|---|",
    ]
)
lines.extend(format_endpoint(endpoint) for endpoint in endpoints)
lines.extend(
    [
        "",
        "## Load Testing",
        "",
        "Results captured in `automation/stage05/metrics.json`:",
        "",
        "```json",
        metrics_excerpt,
        "```",
    ]
)
lines.extend(
    [
        "",
        "## Generated At",
        "",
        datetime.now(timezone.utc).isoformat(),
    ]
)
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "Updating stage status"
"$PYTHON_BIN" - <<'PY' "$STATUS_JSON" "$SUMMARY_JSON"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text(encoding="utf-8"))
backlog = summary.get("backlog_item", {})
feature_flag = summary.get("feature_flag")
now = datetime.now(timezone.utc).isoformat()

artifacts = [
    "backend/app/feature_flags.py",
    "backend/app/api/routes/assets.py",
    "backend/app/repositories/assets.py",
    "backend/app/services/assets.py",
    "backend/app/schemas/assets.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/routes/__init__.py",
    "backend/tests/integration/conftest.py",
    "backend/tests/integration/test_assets.py",
    "backend/loadtests/main.js",
    "docs/api/assets.md",
    "automation/stage05/summary.json",
    "automation/stage05/report.md",
]

payload = {
    "$schema": "../status.schema.json",
    "state": "prepared",
    "checks": [
        {
            "name": "backlog-sync",
            "status": "ok",
            "message": f"Assets domain generated from backlog item {backlog.get('id')}",
        },
        {
            "name": "openapi",
            "status": "ok",
            "message": "backend/openapi.json refreshed",
        },
    ],
    "artifacts": artifacts,
    "last_run": now,
    "warnings": [],
    "notes": ["run.sh executed"],
    "extra": {
        "backlog_item": backlog,
        "feature_flag": feature_flag,
        "documentation": summary.get("documentation"),
    },
}

status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Stage 05 preparation complete"
