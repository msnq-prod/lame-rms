#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
STATUS_FILE_PATH="${STATUS_FILE:-$SCRIPT_DIR/status.json}"

STATUS_FILE="$STATUS_FILE_PATH" "$REPO_ROOT/automation/bin/ensure_tools.sh"

TOOL_TMP=$(mktemp)
CHECKS_FILE=$(mktemp)
WARNINGS_FILE=$(mktemp)
DIFF_FILE=$(mktemp)
trap 'rm -f "$TOOL_TMP" "$CHECKS_FILE" "$WARNINGS_FILE" "$DIFF_FILE"' EXIT

cp "$STATUS_FILE_PATH" "$TOOL_TMP"

FAILED=0

record_check() {
  local name="$1"
  local status="$2"
  local details="$3"
  printf '%s\t%s\t%s\n' "$name" "$status" "$details" >>"$CHECKS_FILE"
  if [[ "$status" == "fail" ]]; then
    FAILED=1
  fi
}

add_warning() {
  printf '%s\n' "$1" >>"$WARNINGS_FILE"
}

tool_summary=$(python3 - "$TOOL_TMP" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
tools = data.get("tools", [])
warnings = [t for t in tools if t.get("status") not in {"ok", "installed"}]
status = "pass" if not warnings else "warn"
message = ", ".join(f"{t['name']}={t['status']}" for t in tools) or "no tools checked"
print(status)
print(message)
PY
)

tool_status=$(printf '%s\n' "$tool_summary" | head -n1)
tool_message=$(printf '%s\n' "$tool_summary" | tail -n +2 | paste -sd ' ' -)
record_check "tooling" "$tool_status" "$tool_message"
if [[ "$tool_status" == "warn" ]]; then
  add_warning "Some optional tools are unavailable: $tool_message"
fi

FILES_JSON="$REPO_ROOT/docs/inventory/files.json"
if [[ -f "$FILES_JSON" ]]; then
  file_check=$(python3 - "$FILES_JSON" "$REPO_ROOT" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

files_json = Path(sys.argv[1])
repo_root = Path(sys.argv[2])
data = json.load(open(files_json, "r", encoding="utf-8"))
sources = data.get("sources", [])
stats = data.get("stats", {})
mismatches = []
for source in sources:
    label = source.get("label")
    rel_path = source.get("path", "")
    target = (repo_root / rel_path).resolve()
    if not target.exists():
        actual_count = 0
    else:
        result = subprocess.run(
            ["find", str(target), "-type", "f"],
            check=True,
            capture_output=True,
            text=True,
        )
        actual_count = len([line for line in result.stdout.splitlines() if line.strip()])
    reported = stats.get(label, {}).get("file_count", 0)
    if reported != actual_count:
        mismatches.append(f"{label}: reported {reported}, actual {actual_count}")

if mismatches:
    print("fail")
    print("; ".join(mismatches))
else:
    totals = sum(stats.get(label, {}).get("file_count", 0) for label in stats)
    print("pass")
    print(f"Inventory covers {totals} files")
PY
  ) || file_check=$'fail\nInventory validation failed'
  file_status=$(printf '%s\n' "$file_check" | head -n1)
  file_message=$(printf '%s\n' "$file_check" | tail -n +2 | paste -sd ' ' -)
  record_check "file_inventory" "$file_status" "$file_message"
else
  record_check "file_inventory" "fail" "docs/inventory/files.json missing"
fi

FILES_CSV="$REPO_ROOT/docs/inventory/files.csv"
if [[ -f "$FILES_CSV" ]] && [[ -f "$FILES_JSON" ]]; then
  csv_check=$(python3 - "$FILES_CSV" "$FILES_JSON" <<'PY'
import csv
import json
import sys

csv_path = sys.argv[1]
json_path = sys.argv[2]

with open(csv_path, "r", encoding="utf-8") as handle:
    reader = csv.reader(handle)
    rows = list(reader)

with open(json_path, "r", encoding="utf-8") as handle:
    data = json.load(handle)

header = rows[0] if rows else []
expected = ["path", "root", "relative_path", "extension", "category", "size_bytes", "line_count", "modified_at"]
if header != expected:
    print("fail")
    print("Unexpected CSV header")
    sys.exit(0)

row_count = len(rows) - 1
json_count = len(data.get("files", []))
if row_count != json_count:
    print("fail")
    print(f"CSV rows {row_count} != JSON entries {json_count}")
else:
    print("pass")
    print(f"CSV rows match JSON entries ({row_count})")
PY
  ) || csv_check=$'fail\nCSV validation failed'
  csv_status=$(printf '%s\n' "$csv_check" | head -n1)
  csv_message=$(printf '%s\n' "$csv_check" | tail -n +2 | paste -sd ' ' -)
  record_check "inventory_csv" "$csv_status" "$csv_message"
else
  record_check "inventory_csv" "fail" "docs/inventory/files.csv missing"
fi

OPENAPI_JSON="$REPO_ROOT/docs/inventory/api/openapi.json"
if [[ -f "$OPENAPI_JSON" ]]; then
  json_check=$(python3 - "$OPENAPI_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)

paths = data.get("paths", {})
if not isinstance(paths, dict):
    print("fail")
    print("OpenAPI paths structure invalid")
elif not paths:
    print("warn")
    print("OpenAPI contains no paths")
else:
    print("pass")
    print(f"OpenAPI exports {len(paths)} paths")
PY
  ) || json_check=$'fail\nOpenAPI validation failed'
  json_status=$(printf '%s\n' "$json_check" | head -n1)
  json_message=$(printf '%s\n' "$json_check" | tail -n +2 | paste -sd ' ' -)
  record_check "openapi_export" "$json_status" "$json_message"
else
  record_check "openapi_export" "fail" "docs/inventory/api/openapi.json missing"
fi

BACKLOG_YAML="$REPO_ROOT/docs/backlog/migration_backlog.yaml"
BACKLOG_JSON="$REPO_ROOT/docs/backlog/migration_backlog.json"
if [[ -f "$BACKLOG_YAML" ]]; then
  if command -v yamllint >/dev/null 2>&1; then
    if yamllint -d '{extends: default, rules: {line-length: {max: 160}, document-start: disable}}' "$BACKLOG_YAML" >/dev/null; then
      yaml_status="pass"
      yaml_message="Backlog YAML validated with yamllint"
    else
      yaml_status="fail"
      yaml_message="yamllint reported issues"
    fi
  else
    yaml_status="warn"
    yaml_message="yamllint not available; syntax not linted"
    add_warning "yamllint not installed; backlog lint skipped"
  fi
  record_check "backlog_yaml" "$yaml_status" "$yaml_message"
else
  record_check "backlog_yaml" "fail" "Backlog file missing"
fi

if [[ -f "$BACKLOG_JSON" ]]; then
  risk_check=$(python3 - "$BACKLOG_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

allowed = {"critical", "high", "medium", "low"}
issues = []
for item in payload.get("items", []):
    risk = item.get("risk", {})
    severity = risk.get("severity")
    if severity not in allowed:
        issues.append(f"{item.get('id')}: severity {severity}")

if issues:
    print("fail")
    print("; ".join(issues))
else:
    print("pass")
    print(f"All {len(payload.get('items', []))} backlog items include severity")
PY
  ) || risk_check=$'fail\nRisk validation failed'
  risk_status=$(printf '%s\n' "$risk_check" | head -n1)
  risk_message=$(printf '%s\n' "$risk_check" | tail -n +2 | paste -sd ' ' -)
  record_check "risk_severity" "$risk_status" "$risk_message"
else
  record_check "risk_severity" "fail" "Backlog JSON missing"
fi

STRUCTURE_DIAGRAM="$REPO_ROOT/docs/inventory/structure.mmd"
API_DIAGRAM="$REPO_ROOT/docs/inventory/api_surface.mmd"
if [[ -s "$STRUCTURE_DIAGRAM" && -s "$API_DIAGRAM" ]]; then
  record_check "diagrams" "pass" "Mermaid diagrams present"
else
  record_check "diagrams" "fail" "Mermaid diagrams missing"
fi

if [[ -f "$REPO_ROOT/docs/inventory/cron.md" ]]; then
  cron_status="pass"
  cron_message="Cron report available"
else
  cron_status="fail"
  cron_message="Cron report missing"
fi
record_check "cron_report" "$cron_status" "$cron_message"

git -C "$REPO_ROOT" status --short docs/inventory docs/backlog automation/stage02/report.md 2>/dev/null >"$DIFF_FILE" || true

SELF_CHECK_FAILED=$FAILED python3 - "$STATUS_FILE_PATH" "$TOOL_TMP" "$CHECKS_FILE" "$WARNINGS_FILE" "$DIFF_FILE" "$FILES_JSON" "$OPENAPI_JSON" "$REPO_ROOT/docs/inventory/cron.md" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
tool_path = Path(sys.argv[2])
checks_path = Path(sys.argv[3])
warnings_path = Path(sys.argv[4])
diff_path = Path(sys.argv[5])
files_json = Path(sys.argv[6]) if sys.argv[6] != '' else None
openapi_json = Path(sys.argv[7]) if sys.argv[7] != '' else None
cron_md = Path(sys.argv[8]) if sys.argv[8] != '' else None

tools_payload = {}
if tool_path.exists():
    tools_payload = json.load(tool_path.open("r", encoding="utf-8"))

checks = {}
with open(checks_path, "r", encoding="utf-8") as handle:
    for line in handle:
        name, status, details = line.rstrip("\n").split("\t", 2)
        checks[name] = {"status": status, "details": details}

warnings = []
if warnings_path.exists():
    with open(warnings_path, "r", encoding="utf-8") as handle:
        warnings = [line.rstrip("\n") for line in handle if line.rstrip("\n")]

diff_summary = []
if diff_path.exists():
    with open(diff_path, "r", encoding="utf-8") as handle:
        diff_summary = [line.rstrip("\n") for line in handle if line.rstrip("\n")]

file_count = 0
if files_json and files_json.exists():
    payload = json.load(files_json.open("r", encoding="utf-8"))
    file_count = len(payload.get("files", []))

api_count = 0
if openapi_json and Path(openapi_json).exists():
    data = json.load(openapi_json.open("r", encoding="utf-8"))
    api_count = len(data.get("paths", {}))

cron_entries = 0
if cron_md and cron_md.exists():
    with open(cron_md, "r", encoding="utf-8") as handle:
        counted = [
            1
            for line in handle
            if line.startswith("| ") and "-" not in line.split("|", 2)[1].strip()
        ]
    cron_entries = max(len(counted) - 1, 0)

state = "ready" if os.environ.get("SELF_CHECK_FAILED", "0") == "0" else "needs_attention"

status_payload = {
    "state": state,
    "checks": checks,
    "artifacts": [
        {"type": "inventory", "path": "docs/inventory/files.json", "description": "File catalogue"},
        {"type": "inventory", "path": "docs/inventory/files.csv", "description": "File catalogue CSV"},
        {"type": "metrics", "path": "docs/inventory/metrics.md", "description": "Metrics summary"},
        {"type": "cron", "path": "docs/inventory/cron.md", "description": "Cron and schedule review"},
        {"type": "api", "path": "docs/inventory/api/openapi.json", "description": "API export"},
        {"type": "backlog", "path": "docs/backlog/migration_backlog.yaml", "description": "Migration backlog"},
        {"type": "report", "path": "automation/stage02/report.md", "description": "Stage report"},
    ],
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": [],
    "extra": {
        "diff_summary": diff_summary,
        "tool_inventory": tools_payload.get("tools", []),
        "file_count_reported": file_count,
        "api_endpoints": api_count,
        "cron_candidates": cron_entries,
    },
}

with open(status_path, "w", encoding="utf-8") as handle:
    json.dump(status_payload, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY

if [[ "$FAILED" -ne 0 ]]; then
  echo "Stage 02 self-check failed" >&2
  exit 1
fi

echo "Stage 02 self-check completed"
