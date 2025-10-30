#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
STATUS_JSON="$SCRIPT_DIR/status.json"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
RESULTS_JSON="$SCRIPT_DIR/results.json"
TOOLS_STATUS_JSON="$SCRIPT_DIR/tools_status.json"
ALERT_SUMMARY_JSON="$SCRIPT_DIR/alert_summary.json"
LOG_DIR="$SCRIPT_DIR/logs"
REPORT_MD="$SCRIPT_DIR/report.md"
ROLE_DOC="$REPO_ROOT/docs/security/roles.md"
POLICY_DOC="$REPO_ROOT/docs/security/policies.md"

mkdir -p "$LOG_DIR"

log() {
  printf '[stage06] %s\n' "$1"
}

log "Ensuring tooling via automation/bin/ensure_tools.sh"
STATUS_FILE="$TOOLS_STATUS_JSON" "$REPO_ROOT/automation/bin/ensure_tools.sh"

log "Running backend auth unit tests"
PYTEST_LOG="$LOG_DIR/pytest_auth.log"
set +e
PYTHONPATH="$REPO_ROOT/backend" pytest "$REPO_ROOT/backend/tests/auth" "$REPO_ROOT/backend/tests/monitoring" -q | tee "$PYTEST_LOG"
PYTEST_EXIT=${PIPESTATUS[0]}
set -e
if [[ $PYTEST_EXIT -eq 0 ]]; then
  PYTEST_STATUS="ok"
  PYTEST_MESSAGE="pytest backend/tests/auth backend/tests/monitoring -q"
else
  PYTEST_STATUS="fail"
  PYTEST_MESSAGE="pytest exit code $PYTEST_EXIT"
fi

log "Running bandit static analysis"
BANDIT_LOG="$LOG_DIR/bandit.log"
if command -v bandit >/dev/null 2>&1; then
  set +e
  bandit -q -r "$REPO_ROOT/backend/app/auth" "$REPO_ROOT/backend/app/monitoring/security.py" >"$BANDIT_LOG" 2>&1
  BANDIT_EXIT=$?
  set -e
  if [[ $BANDIT_EXIT -eq 0 ]]; then
    BANDIT_STATUS="ok"
    BANDIT_MESSAGE="bandit -q -r backend/app/auth backend/app/monitoring/security.py"
  else
    BANDIT_STATUS="fail"
    BANDIT_MESSAGE="bandit exit code $BANDIT_EXIT"
  fi
else
  printf 'bandit executable not found; cannot run static analysis\n' >"$BANDIT_LOG"
  BANDIT_STATUS="fail"
  BANDIT_MESSAGE="bandit not installed"
fi

log "Running npm lint"
NPM_LINT_LOG="$LOG_DIR/npm_lint.log"
if command -v npm >/dev/null 2>&1; then
  set +e
  (cd "$REPO_ROOT/frontend" && npm run lint --silent) | tee "$NPM_LINT_LOG"
  NPM_EXIT=${PIPESTATUS[0]}
  set -e
  if [[ $NPM_EXIT -eq 0 ]]; then
    NPM_STATUS="ok"
    NPM_MESSAGE="npm run lint"
  else
    NPM_STATUS="fail"
    NPM_MESSAGE="npm run lint exit code $NPM_EXIT"
  fi
else
  printf 'npm executable not available; skipping lint\n' >"$NPM_LINT_LOG"
  NPM_STATUS="warning"
  NPM_MESSAGE="npm not installed"
fi

log "Installing Playwright dependencies"
PLAYWRIGHT_SETUP_LOG="$LOG_DIR/playwright_setup.log"
if command -v node >/dev/null 2>&1; then
  set +e
  (cd "$REPO_ROOT/frontend" && node scripts/install_playwright.mjs) | tee "$PLAYWRIGHT_SETUP_LOG"
  PLAYWRIGHT_SETUP_EXIT=${PIPESTATUS[0]}
  set -e
else
  printf 'Node.js executable not found; cannot install Playwright dependencies\n' >"$PLAYWRIGHT_SETUP_LOG"
  PLAYWRIGHT_SETUP_EXIT=127
fi

log "Executing Playwright e2e test"
PLAYWRIGHT_LOG="$LOG_DIR/playwright_auth.log"
if [[ ${PLAYWRIGHT_SETUP_EXIT:-1} -ne 0 ]]; then
  PLAYWRIGHT_STATUS="fail"
  PLAYWRIGHT_MESSAGE="Playwright dependency install exit code ${PLAYWRIGHT_SETUP_EXIT:-1}"
  PLAYWRIGHT_LOG="$PLAYWRIGHT_SETUP_LOG"
elif ! command -v npx >/dev/null 2>&1; then
  printf 'npx executable not available; cannot execute Playwright tests\n' >"$PLAYWRIGHT_LOG"
  PLAYWRIGHT_STATUS="fail"
  PLAYWRIGHT_MESSAGE="npx not installed"
else
  set +e
  (cd "$REPO_ROOT/frontend" && npx playwright test frontend/tests/auth.spec.ts --reporter=list) | tee "$PLAYWRIGHT_LOG"
  PLAYWRIGHT_EXIT=${PIPESTATUS[0]}
  set -e
  if [[ $PLAYWRIGHT_EXIT -eq 0 ]]; then
    PLAYWRIGHT_STATUS="ok"
    PLAYWRIGHT_MESSAGE="Playwright auth.spec.ts"
  else
    PLAYWRIGHT_STATUS="fail"
    PLAYWRIGHT_MESSAGE="Playwright exit code $PLAYWRIGHT_EXIT"
  fi
fi

log "Emulating security alert"
ALERT_LOG="$SCRIPT_DIR/security_alerts.jsonl"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$ALERT_LOG" "$ALERT_SUMMARY_JSON"
import json
import sys
from pathlib import Path
from typing import Optional, Set
from datetime import datetime, timezone

from app.monitoring.security import SecurityMonitor

log_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
monitor = SecurityMonitor(log_path)
monitor.clear()
alert = monitor.emit_alert(
    title="Brute force detected",
    severity="high",
    payload={"source_ip": "203.0.113.10", "attempts": 12},
)
event = monitor.record_event(
    event_type="auth.bruteforce_blocked",
    severity="medium",
    payload={"ip": "203.0.113.10", "blocked_at": datetime.now(timezone.utc).isoformat()},
)
summary = {
    "alert": {
        "title": alert.title,
        "severity": alert.severity,
        "payload": alert.payload,
        "created_at": alert.created_at.isoformat(),
        "log": str(log_path.resolve()),
    },
    "event": {
        "event_type": event.event_type,
        "severity": event.severity,
        "payload": event.payload,
        "recorded_at": event.recorded_at.isoformat(),
    },
}
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
ALERT_STATUS="ok"
ALERT_MESSAGE="Security alert emulated"

log "Collecting results"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$RESULTS_JSON" "$TOOLS_STATUS_JSON" "$PYTEST_STATUS" "$PYTEST_MESSAGE" "$PYTEST_LOG" "$BANDIT_STATUS" "$BANDIT_MESSAGE" "$BANDIT_LOG" "$NPM_STATUS" "$NPM_MESSAGE" "$NPM_LINT_LOG" "$PLAYWRIGHT_STATUS" "$PLAYWRIGHT_MESSAGE" "$PLAYWRIGHT_LOG" "$PLAYWRIGHT_SETUP_LOG" "$ALERT_STATUS" "$ALERT_MESSAGE" "$ALERT_SUMMARY_JSON"
import json
import sys
from pathlib import Path

results_path = Path(sys.argv[1])
tools_status_path = Path(sys.argv[2])
pytest_status = sys.argv[3]
pytest_message = sys.argv[4]
pytest_log = sys.argv[5]
bandit_status = sys.argv[6]
bandit_message = sys.argv[7]
bandit_log = sys.argv[8]
npm_status = sys.argv[9]
npm_message = sys.argv[10]
npm_log = sys.argv[11]
playwright_status = sys.argv[12]
playwright_message = sys.argv[13]
playwright_log = sys.argv[14]
playwright_setup_log = sys.argv[15]
alert_status = sys.argv[16]
alert_message = sys.argv[17]
alert_summary_path = Path(sys.argv[18])

results = {
    "checks": {
        "pytest": {"status": pytest_status, "message": pytest_message, "log": str(Path(pytest_log).resolve())},
        "bandit": {"status": bandit_status, "message": bandit_message, "log": str(Path(bandit_log).resolve())},
        "npm_lint": {"status": npm_status, "message": npm_message, "log": str(Path(npm_log).resolve())},
        "playwright": {
            "status": playwright_status,
            "message": playwright_message,
            "log": str(Path(playwright_log).resolve()),
            "setup_log": str(Path(playwright_setup_log).resolve()),
        },
        "alert_emulation": {"status": alert_status, "message": alert_message, "log": str(alert_summary_path.resolve())},
    },
    "tools": {},
    "alerts": {},
}
if tools_status_path.exists():
    tools_payload = json.loads(tools_status_path.read_text(encoding="utf-8"))
    results["tools"] = tools_payload
if alert_summary_path.exists():
    results["alerts"] = json.loads(alert_summary_path.read_text(encoding="utf-8"))
results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Updating status.json"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$STATUS_JSON" "$SUMMARY_JSON" "$RESULTS_JSON" "$ROLE_DOC" "$POLICY_DOC"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
results_path = Path(sys.argv[3])
role_doc = Path(sys.argv[4])
policy_doc = Path(sys.argv[5])

existing = {}
if status_path.exists():
    existing = json.loads(status_path.read_text(encoding="utf-8"))
summary = json.loads(summary_path.read_text(encoding="utf-8"))
results = json.loads(results_path.read_text(encoding="utf-8"))

checks = [check for check in existing.get("checks", []) if check.get("name") not in {"pytest-auth", "bandit", "npm-lint", "playwright-auth", "alert-emulation"}]
checks.append({"name": "pytest-auth", "status": results["checks"]["pytest"]["status"], "message": results["checks"]["pytest"]["message"], "path": results["checks"]["pytest"]["log"]})
checks.append({"name": "bandit", "status": results["checks"]["bandit"]["status"], "message": results["checks"]["bandit"]["message"], "path": results["checks"]["bandit"]["log"]})
checks.append({"name": "npm-lint", "status": results["checks"]["npm_lint"]["status"], "message": results["checks"]["npm_lint"]["message"], "path": results["checks"]["npm_lint"]["log"]})
checks.append({"name": "playwright-auth", "status": results["checks"]["playwright"]["status"], "message": results["checks"]["playwright"]["message"], "path": results["checks"]["playwright"]["log"]})
checks.append({"name": "alert-emulation", "status": results["checks"]["alert_emulation"]["status"], "message": results["checks"]["alert_emulation"]["message"], "path": results["checks"]["alert_emulation"]["log"]})

artifacts = set(existing.get("artifacts", []))
artifacts.update({
    results["checks"]["pytest"]["log"],
    results["checks"]["bandit"]["log"],
    results["checks"]["npm_lint"]["log"],
    results["checks"]["playwright"]["log"],
    results["checks"]["alert_emulation"]["log"],
    "automation/stage06/results.json",
    "automation/stage06/alert_summary.json",
})
playwright_setup_log = results["checks"]["playwright"].get("setup_log")
if playwright_setup_log:
    artifacts.add(playwright_setup_log)
artifacts.add("automation/stage06/report.md")
artifacts.add("automation/stage06/summary.json")

warnings = existing.get("warnings", [])
tools_payload = results.get("tools", {})
for warning in tools_payload.get("warnings", []):
    if warning not in warnings:
        warnings.append(warning)

def append_tool_warning(tool: str, message: str) -> None:
    candidate = {"tool": tool, "message": message}
    if candidate not in warnings:
        warnings.append(candidate)

for tool_key, tool_name in [
    ("npm_lint", "npm"),
    ("bandit", "bandit"),
    ("playwright", "playwright"),
]:
    status = results["checks"][tool_key]["status"]
    if status in {"warning", "skip", "fail"}:
        append_tool_warning(tool_name, results["checks"][tool_key]["message"])

unique_warnings: list[dict] = []
for warning in warnings:
    if warning not in unique_warnings:
        unique_warnings.append(warning)
warnings = unique_warnings

notes = [
    note
    for note in existing.get("notes", [])
    if not note.startswith(("pytest status=", "bandit status=", "npm status=", "playwright status="))
]
notes.extend([
    "self_check.sh executed",
    f"pytest status={results['checks']['pytest']['status']}",
    f"bandit status={results['checks']['bandit']['status']}",
    f"npm status={results['checks']['npm_lint']['status']}",
    f"playwright status={results['checks']['playwright']['status']}",
])
notes = list(dict.fromkeys(notes))

state = "completed"
check_states = [check.get("status") for check in checks]
if any(status == "fail" for status in check_states):
    state = "failed"
elif any(status in {"warning", "skip"} for status in check_states):
    state = "needs_attention"

extra = existing.get("extra", {})
extra["security_findings"] = results["checks"]["bandit"].get("message")
extra["alerts"] = results.get("alerts", {})
if tools_payload:
    extra["tools_summary"] = tools_payload.get("extra", {}).get("tools_summary", tools_payload.get("tools_summary"))

payload = {
    "$schema": "../status.schema.json",
    "state": state,
    "checks": checks,
    "artifacts": sorted(artifacts),
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": notes,
    "extra": extra,
}
status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Refreshing report with verification results"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$RESULTS_JSON" "$REPORT_MD" "$ROLE_DOC" "$POLICY_DOC"
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
results_path = Path(sys.argv[2])
report_path = Path(sys.argv[3])
role_doc = Path(sys.argv[4])
policy_doc = Path(sys.argv[5])

summary = json.loads(summary_path.read_text(encoding="utf-8"))
results = json.loads(results_path.read_text(encoding="utf-8"))


def safe_relative(path: Path) -> str:
    if not path.exists():
        return str(path)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())

def read_log_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def summarise_bandit(status: str, message: str, log_path: Path) -> list[str]:
    log_lines = read_log_lines(log_path)
    if status == "ok":
        issues = []
        for line in log_lines:
            if line.startswith(">> Issue:"):
                issues.append(line.split(":", 1)[1].strip())
        if issues:
            entries = [f"- Bandit reported {len(issues)} issue(s)."]
            for issue in issues[:5]:
                entries.append(f"  - {issue}")
            if len(issues) > 5:
                entries.append("  - …")
            return entries
        return ["- Bandit completed with no findings."]

    entries = [f"- Bandit status={status}: {message}"]
    for line in log_lines[:5]:
        entries.append(f"  - {line}")
    if not log_lines:
        entries.append("  - No additional log output captured.")
    return entries

def summarise_playwright(status: str, message: str, test_log: Path, setup_log: Optional[Path]) -> list[str]:
    if status == "ok":
        return [f"- Playwright tests passed: {message}"]

    entries = [f"- Playwright status={status}: {message}"]
    seen_paths: Set[Path] = set()
    for path in [setup_log, test_log]:
        if not path:
            continue
        resolved = path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        log_lines = read_log_lines(path)
        label = "setup log" if setup_log and resolved == setup_log.resolve() else "test log"
        if log_lines:
            entries.append(f"  - {label} excerpt:")
            for line in log_lines[:5]:
                entries.append(f"    - {line}")
        else:
            entries.append(f"  - {label}: no additional output captured.")
    return entries

check_rows = []
for name, data in results["checks"].items():
    check_rows.append((name, data["status"], f"{data['message']} ({data['log']})"))

lines = [
    "# Stage 06 Report",
    "",
    "## Summary",
    "- Authentication module implemented with JWT, refresh, MFA, and audit trail.",
    f"- Role definitions synchronised ({len(summary.get('roles', []))} roles).",
]
if summary.get("policy_doc"):
    lines.append(f"- Security policies documented in `{summary['policy_doc']}`.")
else:
    lines.append("- Security policies pending.")
lines.extend(
    [
        "",
        "## Checks",
        "",
        "| Check | Status | Details |",
        "|---|---|---|",
    ]
)
for name, status, message in check_rows:
    lines.append(f"| {name} | {status} | {message} |")
lines.extend(
    [
        "",
        "## Security Findings",
        "",
        "### Bandit",
    ]
)
lines.extend(summarise_bandit(
    results["checks"]["bandit"]["status"],
    results["checks"]["bandit"]["message"],
    Path(results["checks"]["bandit"]["log"]),
))
lines.extend(
    [
        "",
        "### Playwright",
    ]
)
lines.extend(summarise_playwright(
    results["checks"]["playwright"]["status"],
    results["checks"]["playwright"]["message"],
    Path(results["checks"]["playwright"]["log"]),
    Path(results["checks"]["playwright"].get("setup_log", results["checks"]["playwright"]["log"])),
))
lines.extend(
    [
        "",
        "## Security Policy Checklist",
    ]
)
checklist = summary.get("checklist", [])
if checklist:
    lines.extend(checklist)
else:
    lines.append("- [ ] Security checklist pending update")
lines.extend(
    [
        "",
        "## Monitoring",
        f"- Alerts summary: `{results['alerts'].get('alert', {}).get('log', 'n/a')}`.",
        f"- Role matrix: `{safe_relative(role_doc)}`.",
        f"- Policies: `{safe_relative(policy_doc)}`.",
    ]
)
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "Stage 06 self-check complete"
