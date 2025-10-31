#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
STATUS_JSON="$SCRIPT_DIR/status.json"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
REPORT_MD="$SCRIPT_DIR/report.md"
QUEUE_JSON="$SCRIPT_DIR/queue.json"

export APP_CELERY_BROKER_URL="${APP_CELERY_BROKER_URL:-memory://}"
export APP_CELERY_RESULT_BACKEND="${APP_CELERY_RESULT_BACKEND:-cache+memory://}"
export APP_QUEUE_FALLBACK_ENABLED="${APP_QUEUE_FALLBACK_ENABLED:-true}"

log() {
  printf '[stage07] %s\n' "$1"
}

log "Preparing integration cache directories"
mkdir -p "$REPO_ROOT/backend/var/integrations"
mkdir -p "$REPO_ROOT/backend/var/integrations/objects"

log "Compiling integration summary"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$QUEUE_JSON"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings
from app.integrations.registry import get_integrations
from app.integrations.schedule import get_beat_schedule

summary_path = Path(sys.argv[1])
queue_path = Path(sys.argv[2])
settings = get_settings()

integrations = [
    {"name": name, "factory": factory.__name__}
    for name, factory in get_integrations().items()
]
beat_schedule = get_beat_schedule()
queue_config = {
    "broker": settings.celery_broker_url,
    "result_backend": settings.celery_result_backend,
    "default_queue": settings.celery_default_queue,
    "fallback": {
        "enabled": settings.queue_fallback_enabled,
        "broker": settings.celery_fallback_broker_url,
        "result_backend": settings.celery_fallback_result_backend,
    },
}

data = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "integrations": integrations,
    "beat_schedule": {name: {"task": cfg["task"]} for name, cfg in beat_schedule.items()},
    "queue": queue_config,
}
summary_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
queue_path.write_text(json.dumps(queue_config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

log "Updating stage report"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$REPORT_MD"
import json
import sys
from pathlib import Path

summary = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report_path = Path(sys.argv[2])

lines = [
    "# Stage 07 Report",
    "",
    "## Summary",
    "- Integration adapters have been consolidated under `backend/app/integrations`.",
    "- Celery worker, beat scheduler, and in-memory broker configured for local runs (Redis optional).",
    "- Prometheus metrics endpoint exposed at `/api/metrics`.",
    "",
    "## Integrations",
]
for item in summary.get("integrations", []):
    lines.append(f"- `{item['name']}` → {item['factory']}")
lines.extend([
    "",
    "## Queue Configuration",
    f"- Broker: `{summary['queue']['broker']}`",
    f"- Result backend: `{summary['queue']['result_backend']}`",
    f"- Default queue: `{summary['queue']['default_queue']}`",
    "",
    "## Next Steps",
    "- Run `make stage07-verify` to execute Celery checks and integration tests.",
])
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "Writing initial status"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$STATUS_JSON" "$SUMMARY_JSON"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
summary = json.loads(summary_path.read_text(encoding="utf-8"))
now = datetime.now(timezone.utc).isoformat()

payload = {
    "$schema": "../status.schema.json",
    "state": "running",
    "checks": [
        {"name": "integrations", "status": "ok", "message": f"{len(summary['integrations'])} adapters registered"},
    ],
    "artifacts": [
        "automation/stage07/report.md",
        "automation/stage07/summary.json",
        "automation/stage07/queue.json",
        "backend/app/integrations/schedule.py",
    ],
    "last_run": now,
    "warnings": [],
    "notes": ["run.sh executed"],
    "extra": {
        "queue_health": {"state": "unknown"},
        "monitoring": {"metrics_endpoint": "/api/metrics"},
    },
}
status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

log "Stage 07 preparation complete"
