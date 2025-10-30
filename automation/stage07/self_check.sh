#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
VENV_DIR="$REPO_ROOT/backend/.venv"
STATUS_JSON="$SCRIPT_DIR/status.json"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
RESULTS_JSON="$SCRIPT_DIR/results.json"
TOOLS_JSON="$SCRIPT_DIR/tools_status.json"
LOG_DIR="$SCRIPT_DIR/logs"
METRICS_SNAPSHOT="$SCRIPT_DIR/metrics.txt"
QUEUE_PING_LOG="$LOG_DIR/celery_ping.log"
PYTEST_LOG="$LOG_DIR/pytest.log"

mkdir -p "$LOG_DIR"

log() {
  printf '[stage07] %s\n' "$1"
}

log "Ensuring tooling availability"
STATUS_FILE="$TOOLS_JSON" "$REPO_ROOT/automation/bin/ensure_tools.sh" || true

log "Running integration tests"
set +e
PYTHONPATH="$REPO_ROOT/backend" pytest "$REPO_ROOT/backend/tests/integrations" -q | tee "$PYTEST_LOG"
PYTEST_EXIT=${PIPESTATUS[0]}
set -e
if [[ $PYTEST_EXIT -eq 0 ]]; then
  PYTEST_STATUS="ok"
  PYTEST_MESSAGE="pytest backend/tests/integrations -q"
else
  PYTEST_STATUS="fail"
  PYTEST_MESSAGE="pytest exit code $PYTEST_EXIT"
fi

log "Starting Celery worker for ping"
WORKER_STATUS="warning"
WORKER_MESSAGE="celery command unavailable"
PING_STATUS="warning"
PING_MESSAGE="celery not run"
WORKER_PID=""

CELERY_CMD=()
CELERY_NEEDS_PYTHONPATH=0
CELERY_DESC=""
if [[ -x "$VENV_DIR/bin/python" ]] && "$VENV_DIR/bin/python" -c "import celery" >/dev/null 2>&1; then
  CELERY_CMD=("$VENV_DIR/bin/python" -m celery)
  CELERY_NEEDS_PYTHONPATH=1
  CELERY_DESC="python -m celery (.venv)"
elif command -v celery >/dev/null 2>&1; then
  CELERY_CMD=(celery)
  CELERY_DESC="celery binary"
elif "$PYTHON_BIN" -c "import celery" >/dev/null 2>&1; then
  CELERY_CMD=("$PYTHON_BIN" -m celery)
  CELERY_NEEDS_PYTHONPATH=1
  CELERY_DESC="python -m celery ($PYTHON_BIN)"
fi

run_celery() {
  if [[ $CELERY_NEEDS_PYTHONPATH -eq 1 ]]; then
    PYTHONPATH="$REPO_ROOT/backend" "${CELERY_CMD[@]}" "$@"
  else
    "${CELERY_CMD[@]}" "$@"
  fi
}

if [[ ${#CELERY_CMD[@]} -gt 0 ]]; then
  WORKER_STATUS="ok"
  WORKER_MESSAGE="using $CELERY_DESC"
  ORIGINAL_BROKER=${APP_CELERY_BROKER_URL:-}
  ORIGINAL_BACKEND=${APP_CELERY_RESULT_BACKEND:-}
  ORIGINAL_FALLBACK=${APP_QUEUE_FALLBACK_ENABLED:-}
  export APP_CELERY_BROKER_URL="memory://"
  export APP_CELERY_RESULT_BACKEND="cache+memory://"
  export APP_QUEUE_FALLBACK_ENABLED="true"
  WORKER_PID=$( 
    cd "$REPO_ROOT/backend" && {
      run_celery -A app.worker worker --loglevel=info --concurrency=1 --pool=solo >"$LOG_DIR/celery_worker.log" 2>&1 &
      echo $!
    }
  )
  sleep 5
  if [[ $WORKER_PID =~ ^[0-9]+$ ]] && ps -p "$WORKER_PID" >/dev/null 2>&1; then
    set +e
    (
      cd "$REPO_ROOT/backend" && run_celery -A app.worker inspect ping >"$QUEUE_PING_LOG" 2>&1
    )
    PING_EXIT=$?
    set -e
    if [[ $PING_EXIT -eq 0 ]]; then
      PING_STATUS="ok"
      PING_MESSAGE="celery inspect ping"
    else
      PING_STATUS="fail"
      PING_MESSAGE="inspect ping exit code $PING_EXIT"
    fi
  else
    WORKER_STATUS="fail"
    WORKER_MESSAGE="celery worker failed to start ($CELERY_DESC)"
    printf 'celery worker process not running\n' >"$QUEUE_PING_LOG"
  fi
  if [[ $WORKER_PID =~ ^[0-9]+$ ]]; then
    kill "$WORKER_PID" >/dev/null 2>&1 || true
    wait "$WORKER_PID" 2>/dev/null || true
  fi
  if [[ -n "$ORIGINAL_BROKER" ]]; then
    export APP_CELERY_BROKER_URL="$ORIGINAL_BROKER"
  else
    unset APP_CELERY_BROKER_URL
  fi
  if [[ -n "$ORIGINAL_BACKEND" ]]; then
    export APP_CELERY_RESULT_BACKEND="$ORIGINAL_BACKEND"
  else
    unset APP_CELERY_RESULT_BACKEND
  fi
  if [[ -n "$ORIGINAL_FALLBACK" ]]; then
    export APP_QUEUE_FALLBACK_ENABLED="$ORIGINAL_FALLBACK"
  else
    unset APP_QUEUE_FALLBACK_ENABLED
  fi
else
  printf 'celery command missing; skipping worker ping\n' >"$QUEUE_PING_LOG"
fi

log "Capturing metrics snapshot"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$METRICS_SNAPSHOT"
from pathlib import Path

from app.monitoring.metrics import render_metrics

Path(__import__("sys").argv[1]).write_text(render_metrics().rstrip("\n") + "\n", encoding="utf-8")
PY

log "Compiling results payload"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$RESULTS_JSON" "$TOOLS_JSON" "$PYTEST_STATUS" "$PYTEST_MESSAGE" "$PYTEST_LOG" "$WORKER_STATUS" "$WORKER_MESSAGE" "$PING_STATUS" "$PING_MESSAGE" "$QUEUE_PING_LOG" "$METRICS_SNAPSHOT"
import json
import sys
from pathlib import Path

results_path = Path(sys.argv[1])
tools_path = Path(sys.argv[2])
pytest_status = sys.argv[3]
pytest_message = sys.argv[4]
pytest_log = Path(sys.argv[5]).resolve()
worker_status = sys.argv[6]
worker_message = sys.argv[7]
ping_status = sys.argv[8]
ping_message = sys.argv[9]
ping_log = Path(sys.argv[10]).resolve()
metrics_snapshot = Path(sys.argv[11]).resolve()

tools = {}
if tools_path.exists():
    tools = json.loads(tools_path.read_text(encoding="utf-8"))

payload = {
    "checks": {
        "pytest": {"status": pytest_status, "message": pytest_message, "log": str(pytest_log)},
        "celery_worker": {"status": worker_status, "message": worker_message},
        "celery_ping": {"status": ping_status, "message": ping_message, "log": str(ping_log)},
    },
    "tools": tools,
    "artifacts": {
        "pytest_log": str(pytest_log),
        "celery_ping": str(ping_log),
        "metrics": str(metrics_snapshot),
    },
}
results_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

log "Updating status.json"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$STATUS_JSON" "$SUMMARY_JSON" "$RESULTS_JSON"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
results_path = Path(sys.argv[3])

summary = json.loads(summary_path.read_text(encoding="utf-8"))
results = json.loads(results_path.read_text(encoding="utf-8"))

checks = []
failed = False
for name, detail in results["checks"].items():
    status = detail["status"]
    checks.append({"name": name, "status": status if status in {"ok", "warning", "skip"} else "fail", "message": detail["message"], "path": detail.get("log")})
    if status not in {"ok", "warning", "skip"}:
        failed = True

worker_check = results["checks"].get("celery_worker", {"status": "unknown", "message": "missing"})
ping_check = results["checks"].get("celery_ping", {"status": "unknown", "message": "missing"})
queue_ok = worker_check.get("status") == "ok" and ping_check.get("status") == "ok"

state = "completed" if (not failed and queue_ok) else "needs_attention"
now = datetime.now(timezone.utc).isoformat()

def _fmt_queue(detail):
    message = detail.get("message")
    if message:
        return f"{detail.get('status')}: {message}"
    return str(detail.get("status"))

queue_health = {
    "worker": worker_check,
    "ping": ping_check,
    "status": "ok" if queue_ok else "needs_attention",
}
if not queue_ok:
    queue_health["summary"] = f"worker={_fmt_queue(worker_check)}; ping={_fmt_queue(ping_check)}"

extra = {
    "queue_health": queue_health,
    "monitoring": {
        "metrics_file": results["artifacts"]["metrics"],
    },
}

payload = {
    "$schema": "../status.schema.json",
    "state": state,
    "checks": checks,
    "artifacts": [
        "automation/stage07/report.md",
        "automation/stage07/summary.json",
        results["artifacts"]["pytest_log"],
        results["artifacts"]["celery_ping"],
        results["artifacts"]["metrics"],
    ],
    "last_run": now,
    "warnings": results.get("tools", {}).get("warnings", []),
    "notes": ["self_check.sh executed"],
    "extra": extra,
}
status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

log "Stage 07 self-check complete"
