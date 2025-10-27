#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
STATUS_JSON="$SCRIPT_DIR/status.json"
TOOLS_STATUS="$SCRIPT_DIR/tools_status.json"
METRICS_JSON="$SCRIPT_DIR/metrics.json"
CONTRACT_DIFF="$SCRIPT_DIR/contract_diff.json"
PYTEST_LOG="$SCRIPT_DIR/logs/pytest_integration.log"
K6_LOG="$SCRIPT_DIR/logs/k6.log"
UVICORN_LOG="$SCRIPT_DIR/logs/uvicorn.log"
SCHEMATHESIS_LOG="$SCRIPT_DIR/logs/schemathesis.log"
SCHEMATHESIS_UVICORN_LOG="$SCRIPT_DIR/logs/uvicorn_schemathesis.log"
SCHEMATHESIS_SUMMARY="$SCRIPT_DIR/schemathesis_summary.json"
ALLURE_RESULTS="$SCRIPT_DIR/allure-results"
HTML_REPORT="$SCRIPT_DIR/pytest_integration.html"

mkdir -p "$SCRIPT_DIR/logs" "$ALLURE_RESULTS"

log() {
  printf '[stage05] %s\n' "$1"
}

log "Checking required tooling"
STATUS_FILE="$TOOLS_STATUS" "$REPO_ROOT/automation/bin/ensure_tools.sh"

log "Running integration tests"
PYTEST_CMD=(pytest "$REPO_ROOT/backend/tests/integration" -q)
ALLURE_AVAILABLE=0
if pytest --help | grep -q -- '--alluredir'; then
  ALLURE_AVAILABLE=1
  rm -rf "$ALLURE_RESULTS"
  mkdir -p "$ALLURE_RESULTS"
  PYTEST_CMD+=(--alluredir "$ALLURE_RESULTS")
else
  rm -rf "$ALLURE_RESULTS"
  mkdir -p "$ALLURE_RESULTS"
fi

set +e
"${PYTEST_CMD[@]}" | tee "$PYTEST_LOG"
PYTEST_EXIT=${PIPESTATUS[0]}
set -e

if [[ $ALLURE_AVAILABLE -eq 0 ]]; then
  cat <<'JSON' >"$ALLURE_RESULTS/placeholder.json"
{
  "status": "warning",
  "message": "Allure plugin not installed; results collected as plain log."
}
JSON
fi

log "Building HTML summary for pytest run"
"$PYTHON_BIN" - <<'PY' "$PYTEST_LOG" "$HTML_REPORT" "$PYTEST_EXIT"
import html
import sys
from datetime import datetime, timezone
from pathlib import Path

log_path = Path(sys.argv[1])
html_path = Path(sys.argv[2])
exit_code = int(sys.argv[3])
content = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
status = "passed" if exit_code == 0 else "failed"
html_path.write_text(
    "\n".join(
        [
            "<html>",
            "<head><title>Stage 05 Pytest Integration</title></head>",
            "<body>",
            f"<h1>Pytest integration run ({status})</h1>",
            f"<p>Generated at {datetime.now(timezone.utc).isoformat()}</p>",
            "<pre>",
            html.escape(content),
            "</pre>",
            "</body>",
            "</html>",
        ]
    ),
    encoding="utf-8",
)
PY

PYTEST_STATUS="ok"
if [[ $PYTEST_EXIT -ne 0 ]]; then
  PYTEST_STATUS="fail"
fi

log "Running schemathesis contract checks"
SCHEMATHESIS_STATUS="skip"
SCHEMATHESIS_EXIT=0
SCHEMATHESIS_MESSAGE="schemathesis not available"
SCHEMATHESIS_SCHEMA="backend/openapi.json"
SCHEMATHESIS_PORT=${SCHEMATHESIS_PORT:-8060}
SCHEMATHESIS_BASE_URL="http://127.0.0.1:${SCHEMATHESIS_PORT}"
if command -v schemathesis >/dev/null 2>&1; then
  SCHEMATHESIS_STATUS="ok"
  SCHEMATHESIS_MESSAGE="schemathesis run succeeded"
  : >"$SCHEMATHESIS_LOG"
  : >"$SCHEMATHESIS_UVICORN_LOG"
  set +e
  PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port "$SCHEMATHESIS_PORT" --log-level warning >"$SCHEMATHESIS_UVICORN_LOG" 2>&1 &
  UVICORN_CONTRACT_PID=$!
  sleep 2
  schemathesis run "$REPO_ROOT/$SCHEMATHESIS_SCHEMA" --base-url "$SCHEMATHESIS_BASE_URL" --checks=all --hypothesis-deadline=500 --hypothesis-suppress-health-check=too_slow >"$SCHEMATHESIS_LOG" 2>&1
  SCHEMATHESIS_EXIT=${PIPESTATUS[0]:-1}
  kill "$UVICORN_CONTRACT_PID" >/dev/null 2>&1 || true
  wait "$UVICORN_CONTRACT_PID" >/dev/null 2>&1 || true
  set -e
  if [[ $SCHEMATHESIS_EXIT -ne 0 ]]; then
    SCHEMATHESIS_STATUS="fail"
    SCHEMATHESIS_MESSAGE="schemathesis run reported non-zero exit code"
  fi
else
  printf 'schemathesis executable not available; skipping contract tests\n' >"$SCHEMATHESIS_LOG"
fi

"$PYTHON_BIN" - <<'PY' "$SCHEMATHESIS_SUMMARY" "$SCHEMATHESIS_SCHEMA" "$SCHEMATHESIS_BASE_URL" "$SCHEMATHESIS_STATUS" "$SCHEMATHESIS_EXIT" "$SCHEMATHESIS_MESSAGE"
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
schema = sys.argv[2]
base_url = sys.argv[3]
status = sys.argv[4]
exit_code = int(sys.argv[5])
message = sys.argv[6]

payload = {
    "schema": schema,
    "base_url": base_url,
    "status": status,
    "exit_code": exit_code,
    "message": message,
}
summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

export SCHEMATHESIS_STATUS
export SCHEMATHESIS_EXIT_CODE=$SCHEMATHESIS_EXIT
export SCHEMATHESIS_MESSAGE
export SCHEMATHESIS_LOG_PATH="automation/stage05/logs/schemathesis.log"
export SCHEMATHESIS_SUMMARY_PATH="automation/stage05/schemathesis_summary.json"
export SCHEMATHESIS_UVICORN_LOG_PATH="automation/stage05/logs/uvicorn_schemathesis.log"

log "Executing k6 load test scenario"
K6_STATUS="skip"
K6_EXIT=0
K6_MESSAGE="k6 not available"
if command -v k6 >/dev/null 2>&1; then
  K6_STATUS="ok"
  K6_MESSAGE=""
  : >"$METRICS_JSON"
  set +e
  PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8050 --log-level warning >"$UVICORN_LOG" 2>&1 &
  UVICORN_PID=$!
  sleep 2
  k6 run --summary-export "$METRICS_JSON" --env API_BASE_URL="http://127.0.0.1:8050/api" "$REPO_ROOT/backend/loadtests/main.js" | tee "$K6_LOG"
  K6_EXIT=${PIPESTATUS[0]}
  kill "$UVICORN_PID" >/dev/null 2>&1 || true
  wait "$UVICORN_PID" >/dev/null 2>&1 || true
  set -e
  if [[ $K6_EXIT -ne 0 ]]; then
    K6_STATUS="fail"
    K6_MESSAGE="k6 run reported non-zero exit code"
  fi
else
  cat <<'JSON' >"$METRICS_JSON"
{
  "status": "skipped",
  "message": "k6 executable is not available on this host"
}
JSON
fi

log "Diffing OpenAPI contracts"
"$PYTHON_BIN" - <<'PY' "$REPO_ROOT/backend/openapi.json" "$REPO_ROOT/docs/inventory/api/openapi.json" "$CONTRACT_DIFF"
import json
import sys
from pathlib import Path

new_path = Path(sys.argv[1])
legacy_path = Path(sys.argv[2])
output_path = Path(sys.argv[3])

def load_openapi(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

new_spec = load_openapi(new_path)
legacy_spec = load_openapi(legacy_path)

new_paths = new_spec.get("paths", {})
legacy_paths = legacy_spec.get("paths", {})

def expand_paths(data: dict[str, dict]) -> dict[tuple[str, str], dict]:
    result: dict[tuple[str, str], dict] = {}
    for path, methods in data.items():
        for method, definition in (methods or {}).items():
            key = (method.upper(), path)
            result[key] = definition or {}
    return result

new_map = expand_paths(new_paths)
legacy_map = expand_paths(legacy_paths)

def relevant(keys: set[tuple[str, str]]) -> list[tuple[str, str]]:
    return sorted(key for key in keys if key[1].startswith("/api/assets"))

added_keys = relevant(set(new_map.keys()) - set(legacy_map.keys()))
removed_keys = relevant(set(legacy_map.keys()) - set(new_map.keys()))
common = relevant(set(new_map.keys()) & set(legacy_map.keys()))

payload = {
    "added": [
        {
            "method": method,
            "path": path,
            "summary": new_map[(method, path)].get("summary"),
        }
        for method, path in added_keys
    ],
    "missing_in_new": [
        {
            "method": method,
            "path": path,
            "summary": legacy_map[(method, path)].get("summary"),
        }
        for method, path in removed_keys
    ],
    "unchanged": len(common),
    "summary": {
        "new_total": len(new_map),
        "legacy_total": len(legacy_map),
    },
}

output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Refreshing stage report with latest metrics"
"$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$SCRIPT_DIR/report.md" "$METRICS_JSON"
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

metrics_excerpt = "Metrics not available."
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

export PYTEST_EXIT_CODE=$PYTEST_EXIT
export PYTEST_STATUS
export ALLURE_AVAILABLE
export K6_STATUS
export K6_EXIT_CODE=$K6_EXIT
export K6_MESSAGE
export UVICORN_LOG_PATH="automation/stage05/logs/uvicorn.log"

log "Writing updated status.json"
"$PYTHON_BIN" - <<'PY' "$STATUS_JSON" "$SUMMARY_JSON" "$TOOLS_STATUS" "$CONTRACT_DIFF" "$METRICS_JSON" "$PYTEST_LOG" "$HTML_REPORT" "$ALLURE_RESULTS" "$K6_LOG" "$SCHEMATHESIS_SUMMARY"
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
tools_path = Path(sys.argv[3])
contract_path = Path(sys.argv[4])
metrics_path = Path(sys.argv[5])
pytest_log = Path(sys.argv[6])
html_report = Path(sys.argv[7])
allure_dir = Path(sys.argv[8])
k6_log = Path(sys.argv[9])
schemathesis_summary_path = Path(sys.argv[10])

summary = json.loads(summary_path.read_text(encoding="utf-8"))
backlog = summary.get("backlog_item", {})
feature_flag = summary.get("feature_flag")

tools_payload: dict | None = None
if tools_path.exists():
    tools_payload = json.loads(tools_path.read_text(encoding="utf-8"))

contract_diff = {}
if contract_path.exists():
    contract_diff = json.loads(contract_path.read_text(encoding="utf-8"))

metrics_data = "not collected"
if metrics_path.exists():
    try:
        metrics_data = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        metrics_data = metrics_path.read_text(encoding="utf-8")

schemathesis_summary: Dict[str, Any] = {}
if schemathesis_summary_path.exists():
    schemathesis_summary = json.loads(schemathesis_summary_path.read_text(encoding="utf-8"))

schemathesis_status_env = os.environ.get("SCHEMATHESIS_STATUS")
if schemathesis_status_env:
    schemathesis_summary["status"] = schemathesis_status_env

schemathesis_exit_env = os.environ.get("SCHEMATHESIS_EXIT_CODE")
if schemathesis_exit_env is not None:
    try:
        schemathesis_summary["exit_code"] = int(schemathesis_exit_env)
    except ValueError:
        schemathesis_summary["exit_code"] = schemathesis_exit_env

schemathesis_message_env = os.environ.get("SCHEMATHESIS_MESSAGE")
if schemathesis_message_env:
    schemathesis_summary["message"] = schemathesis_message_env

schemathesis_status = schemathesis_summary.get("status", "skip")
schemathesis_message = schemathesis_summary.get("message", "schemathesis run not executed")

pytest_status = os.environ.get("PYTEST_STATUS", "fail")
pytest_exit = int(os.environ.get("PYTEST_EXIT_CODE", "1"))
allure_available = os.environ.get("ALLURE_AVAILABLE", "0") == "1"
k6_status = os.environ.get("K6_STATUS", "skip")
k6_exit = int(os.environ.get("K6_EXIT_CODE", "0"))
k6_message = os.environ.get("K6_MESSAGE", "")

checks: List[Dict[str, str]] = []
warnings: List[Dict[str, str]] = []
extra: Dict[str, Any] = {
    "contract_diff": contract_diff,
    "performance": metrics_data,
    "test_artifacts": {
        "pytest_log": str(pytest_log.relative_to(Path.cwd())) if pytest_log.exists() else None,
        "html_report": str(html_report.relative_to(Path.cwd())) if html_report.exists() else None,
        "allure_results": str(allure_dir.relative_to(Path.cwd())) if allure_dir.exists() else None,
        "schemathesis_log": os.environ.get("SCHEMATHESIS_LOG_PATH"),
        "schemathesis_summary": str(schemathesis_summary_path.relative_to(Path.cwd())) if schemathesis_summary_path.exists() else None,
    },
    "contract_tests": schemathesis_summary,
}

if tools_payload:
    checks.extend(tools_payload.get("checks", []))
    warnings.extend(tools_payload.get("warnings", []))
    tools_summary = tools_payload.get("extra", {}).get("tools_summary")
    if tools_summary:
        extra["tools_summary"] = tools_summary

checks.append(
    {
        "name": "pytest-integration",
        "status": "ok" if pytest_status == "ok" else "fail",
        "message": "pytest backend/tests/integration -q",
    }
)

if not allure_available:
    warnings.append({"tool": "pytest", "message": "Allure plugin missing; used log/HTML fallback"})

if k6_status == "ok" and k6_exit == 0:
    checks.append({"name": "k6-load", "status": "ok", "message": "k6 run backend/loadtests/main.js"})
elif k6_status == "fail":
    checks.append({"name": "k6-load", "status": "fail", "message": k6_message or "k6 run failed"})
else:
    checks.append({"name": "k6-load", "status": "skip", "message": k6_message})
    warnings.append({"tool": "k6", "message": k6_message})

checks.append(
    {
        "name": "contract-diff",
        "status": "ok",
        "message": "Compared backend/openapi.json with legacy specification",
    }
)

schemathesis_check_message = schemathesis_message or "schemathesis contract tests"
if schemathesis_status == "ok":
    checks.append({"name": "schemathesis-contract", "status": "ok", "message": schemathesis_check_message})
elif schemathesis_status == "fail":
    checks.append({"name": "schemathesis-contract", "status": "fail", "message": schemathesis_check_message})
else:
    checks.append({"name": "schemathesis-contract", "status": "skip", "message": schemathesis_check_message})
    warnings.append({"tool": "schemathesis", "message": schemathesis_check_message})

state = "completed"
if any(check.get("status") == "fail" for check in checks):
    state = "failed"
elif warnings:
    state = "needs_attention"

artifacts = [
    "automation/stage05/report.md",
    "automation/stage05/summary.json",
    "automation/stage05/metrics.json",
    "automation/stage05/contract_diff.json",
    "automation/stage05/logs/pytest_integration.log",
    "automation/stage05/pytest_integration.html",
    "automation/stage05/logs/schemathesis.log",
    "automation/stage05/schemathesis_summary.json",
]
if k6_log.exists():
    artifacts.append("automation/stage05/logs/k6.log")
if UVICORN_LOG := os.environ.get("UVICORN_LOG_PATH"):
    artifacts.append(UVICORN_LOG)
if SCHEMATHESIS_UVICORN_LOG := os.environ.get("SCHEMATHESIS_UVICORN_LOG_PATH"):
    artifacts.append(SCHEMATHESIS_UVICORN_LOG)

payload = {
    "$schema": "../status.schema.json",
    "state": state,
    "checks": checks,
    "artifacts": artifacts,
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": [
        "self_check.sh executed",
        f"pytest exit={pytest_exit}",
        f"k6 status={k6_status}",
        f"schemathesis status={schemathesis_status}",
    ],
    "extra": extra | {
        "backlog_item": backlog,
        "feature_flag": feature_flag,
    },
}

status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Stage 05 self-check complete"
