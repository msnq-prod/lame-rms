#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
STATUS_FILE="$SCRIPT_DIR/status.json"
REPORT_FILE="$SCRIPT_DIR/report.md"
CHECKLIST_FILE="$REPO_ROOT/docs/checklists/stage01.md"
MANIFEST_FILE="$SCRIPT_DIR/created_files.txt"
ARTIFACT_DIR="$SCRIPT_DIR/artifacts"
mkdir -p "$ARTIFACT_DIR"

export PATH="$HOME/.local/bin:$PATH"

APPLY_ENFORCED=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY_ENFORCED=1
      shift
      ;;
    -h|--help)
      cat <<'USAGE'
Usage: automation/stage01/self_check.sh [--apply]

  --apply  Require that legacy/ contains migrated PHP files (after running prepare_legacy.sh).
USAGE
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

log() {
  printf '[stage01:self-check] %s\n' "$1"
}

record_check() {
  local name="$1"
  local status="$2"
  local message="$3"
  message=${message//$'\t'/ }
  printf '%s\t%s\t%s\n' "$name" "$status" "$message" >>"$CHECKS_TSV"
}

record_warning() {
  local tool="$1"
  local message="$2"
  message=${message//$'\t'/ }
  printf '%s\t%s\n' "$tool" "$message" >>"$WARNINGS_FILE"
}

CHECKS_TSV="$ARTIFACT_DIR/checks.tsv"
WARNINGS_FILE="$ARTIFACT_DIR/warnings.tsv"
: >"$CHECKS_TSV"
: >"$WARNINGS_FILE"
printf 'name\tstatus\tmessage\n' >"$CHECKS_TSV"
printf 'tool\tmessage\n' >"$WARNINGS_FILE"

log "Ensuring optional tooling availability"
STATUS_SNAPSHOT="$ARTIFACT_DIR/tools_status.json"
export STATUS_FILE
"$REPO_ROOT/automation/bin/ensure_tools.sh" >"$ARTIFACT_DIR/ensure_tools.log" 2>&1 || true
if [[ -f "$STATUS_FILE" ]]; then
  cp "$STATUS_FILE" "$STATUS_SNAPSHOT"
else
  record_warning "ensure_tools" "automation/bin/ensure_tools.sh did not produce $STATUS_FILE"
fi

structure_check() {
  local missing_paths=()
  local gitkeep_missing=()
  local required_dirs=(backend frontend infrastructure docs docs/checklists legacy scripts)
  for dir in "${required_dirs[@]}"; do
    if [[ ! -d "$REPO_ROOT/$dir" ]]; then
      missing_paths+=("$dir")
    fi
  done
  local keep_dirs=(backend frontend infrastructure legacy)
  for dir in "${keep_dirs[@]}"; do
    if [[ ! -f "$REPO_ROOT/$dir/.gitkeep" ]]; then
      gitkeep_missing+=("$dir/.gitkeep")
    fi
  done
  if [[ ${#missing_paths[@]} -eq 0 && ${#gitkeep_missing[@]} -eq 0 ]]; then
    record_check "structure" "ok" "Required directories and .gitkeep files present"
  else
    local detail=""
    if [[ ${#missing_paths[@]} -gt 0 ]]; then
      detail+="Missing directories: ${missing_paths[*]}. "
    fi
    if [[ ${#gitkeep_missing[@]} -gt 0 ]]; then
      detail+="Missing .gitkeep files: ${gitkeep_missing[*]}."
    fi
    record_check "structure" "fail" "$detail"
  fi
}

manifest_check() {
  if [[ ! -f "$MANIFEST_FILE" ]]; then
    record_check "manifest" "fail" "Manifest file $MANIFEST_FILE missing"
    return
  fi
  local missing=()
  while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if [[ ! -e "$REPO_ROOT/$rel" ]]; then
      missing+=("$rel")
    fi
  done <"$MANIFEST_FILE"
  if [[ ${#missing[@]} -eq 0 ]]; then
    record_check "manifest" "ok" "All manifest entries exist"
  else
    record_check "manifest" "fail" "Missing manifest entries: ${missing[*]}"
  fi
}

legacy_check() {
  local marker="$REPO_ROOT/legacy/.migration_applied"
  local should_verify=$APPLY_ENFORCED
  if [[ -f "$marker" ]]; then
    should_verify=1
  fi
  if [[ "$should_verify" -ne 1 ]]; then
    record_check "legacy-transfer" "skip" "Legacy transfer not enforced"
    return
  fi
  local required=(src db composer.json composer.lock phinx.php migrate.sh php-fpm.conf Dockerfile docker-compose.yml app.json)
  local missing=()
  for item in "${required[@]}"; do
    if [[ ! -e "$REPO_ROOT/legacy/$item" ]]; then
      missing+=("legacy/$item")
    fi
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    record_check "legacy-transfer" "ok" "Legacy assets present in legacy/"
  else
    record_check "legacy-transfer" "fail" "Missing legacy assets: ${missing[*]}"
  fi
}

install_pre_commit_if_needed() {
  if command -v pre-commit >/dev/null 2>&1; then
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    log "Installing pre-commit via pip"
    if python3 -m pip install --user --quiet pre-commit; then
      hash -r
    else
      record_warning "pre-commit" "Failed to install pre-commit via pip"
    fi
  else
    record_warning "python3" "python3 not available to install pre-commit"
  fi
}

pre_commit_check() {
  local log_file="$ARTIFACT_DIR/pre-commit.log"
  install_pre_commit_if_needed
  if ! command -v pre-commit >/dev/null 2>&1; then
    printf 'pre-commit not available\n' >"$log_file"
    record_check "pre-commit" "warning" "pre-commit command unavailable"
    record_warning "pre-commit" "pre-commit command unavailable"
    return
  fi
  log "Running pre-commit"
  set +e
  pre-commit run --all-files >"$log_file" 2>&1
  local exit_code=$?
  set -e
  if [[ $exit_code -eq 0 ]]; then
    record_check "pre-commit" "ok" "pre-commit run succeeded"
  else
    record_check "pre-commit" "fail" "pre-commit run failed (exit $exit_code)"
  fi
}

bootstrap_check() {
  local log_file="$ARTIFACT_DIR/bootstrap-dev.log"
  log "Running make bootstrap-dev"
  set +e
  make -C "$REPO_ROOT" bootstrap-dev >"$log_file" 2>&1
  local exit_code=$?
  set -e
  if [[ $exit_code -eq 0 ]]; then
    record_check "bootstrap-dev" "ok" "make bootstrap-dev succeeded"
  else
    record_check "bootstrap-dev" "fail" "make bootstrap-dev failed (exit $exit_code)"
  fi
}

checklist_validation() {
  local log_file="$ARTIFACT_DIR/checklist.log"
  if [[ ! -f "$CHECKLIST_FILE" ]]; then
    printf 'Checklist file missing\n' >"$log_file"
    record_check "checklist" "fail" "Checklist file missing"
    return
  fi
  python3 - "$CHECKLIST_FILE" >"$log_file" 2>&1 <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Parse YAML front matter manually (simple mapping)
if not text.startswith("---\n"):
    print("Missing YAML front matter", file=sys.stderr)
    sys.exit(1)

parts = text.split("---", 2)
if len(parts) < 3:
    print("Invalid front matter", file=sys.stderr)
    sys.exit(1)
front_matter = parts[1]
content = parts[2]
items = []
current = None
in_items = False
for raw in front_matter.splitlines():
    line = raw.rstrip()
    stripped = line.strip()
    if not in_items:
        if stripped.startswith("items"):
            in_items = True
        continue
    if not stripped:
        continue
    if stripped.startswith("- "):
        if current:
            items.append(current)
        current = {}
        stripped = stripped[2:]
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            current[key.strip()] = value.strip()
        continue
    if current is None:
        continue
    if ":" in stripped:
        key, _, value = stripped.partition(":")
        current[key.strip()] = value.strip()
if current:
    items.append(current)

done_flags = []
for item in items:
    done_flags.append(item.get("done", "false").lower() in {"true", "yes", "1"})

checkboxes = re.findall(r"\[(.)\]", content)
checkbox_done = all(mark.lower() == "x" for mark in checkboxes) if checkboxes else False

if all(done_flags) and checkbox_done:
    print("Checklist complete")
    sys.exit(0)

missing = [item.get("id", "unknown") for idx, item in enumerate(items) if not done_flags[idx]]
if not checkbox_done:
    missing.append("checkboxes")
print("Incomplete checklist entries: " + ", ".join(missing))
sys.exit(1)
PY
  local exit_code=$?
  if [[ $exit_code -eq 0 ]]; then
    record_check "checklist" "ok" "Checklist fully completed"
  else
    record_check "checklist" "fail" "Checklist not fully completed"
  fi
}

act_check() {
  local log_file="$ARTIFACT_DIR/act.log"
  if ! command -v act >/dev/null 2>&1; then
    printf 'act command not available\n' >"$log_file"
    record_check "act" "warning" "act command unavailable"
    record_warning "act" "act command unavailable"
    return
  fi
  log "Running act --dryrun"
  set +e
  act --dryrun >"$log_file" 2>&1
  local exit_code=$?
  set -e
  if [[ $exit_code -eq 0 ]]; then
    record_check "act" "ok" "act --dryrun succeeded"
  else
    record_check "act" "fail" "act --dryrun failed (exit $exit_code)"
  fi
}

structure_check
manifest_check
legacy_check
pre_commit_check
bootstrap_check
checklist_validation
act_check

update_report() {
  local timestamp
  timestamp=$(date -u '+%Y-%m-%d %H:%M:%SZ')
  local pre_commit_log="$ARTIFACT_DIR/pre-commit.log"
  local act_log="$ARTIFACT_DIR/act.log"
  local bootstrap_log="$ARTIFACT_DIR/bootstrap-dev.log"
  python3 - "$REPORT_FILE" "$CHECKS_TSV" "$WARNINGS_FILE" "$pre_commit_log" "$act_log" "$bootstrap_log" "$timestamp" "$MANIFEST_FILE" <<'PY'
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
checks_path = Path(sys.argv[2])
warnings_path = Path(sys.argv[3])
pre_commit_log = Path(sys.argv[4])
act_log = Path(sys.argv[5])
bootstrap_log = Path(sys.argv[6])
timestamp = sys.argv[7]
manifest_path = Path(sys.argv[8])

pre_text = pre_commit_log.read_text() if pre_commit_log.exists() else "<no output>"
act_text = act_log.read_text() if act_log.exists() else "<no output>"
bootstrap_text = bootstrap_log.read_text() if bootstrap_log.exists() else "<no output>"

checks = [line.strip().split("\t") for line in checks_path.read_text().splitlines()[1:] if line.strip()]
status_summary = {}
for name, status, _ in checks:
    status_summary.setdefault(status, 0)
    status_summary[status] += 1

def format_code_block(text):
    text = text.rstrip()
    if not text:
        text = "(no output)"
    return "```\n" + text + "\n```"

if manifest_path.exists():
    lines = [line.strip() for line in manifest_path.read_text().splitlines() if line.strip()]
    created_section = "\n".join(f"- `{line}`" for line in lines)
else:
    created_section = "- (manifest missing)"

warnings = []
if warnings_path.exists():
    for raw in warnings_path.read_text().splitlines()[1:]:
        raw = raw.strip()
        if not raw:
            continue
        tool, _, message = raw.partition("\t")
        warnings.append({"tool": tool, "message": message})

summary_lines = [
    f"- Verification executed at {timestamp}.",
    f"- Checks summary: " + ", ".join(f"{status}={count}" for status, count in sorted(status_summary.items())),
]
if warnings:
    summary_lines.append("- Warnings: " + "; ".join(f"{w['tool']}: {w['message']}" for w in warnings))

content = f"# Summary\n\n" + "\n".join(summary_lines) + "\n\n"
content += "# Created files\n\n" + created_section + "\n\n"
content += "# Checks\n\n"
content += "## pre-commit run --all-files\n\n" + format_code_block(pre_text) + "\n\n"
content += "## make bootstrap-dev\n\n" + format_code_block(bootstrap_text) + "\n\n"
content += "## act --dryrun\n\n" + format_code_block(act_text) + "\n"
content += "\n# Next Gate\n\n- Execute `automation/stage01/prepare_legacy.sh` to move the PHP monolith when ready.\n- Rerun `make stage01-verify` and `make stage01-report` after applying the migration.\n"

report_path.write_text(content)
PY
}

update_report

update_status() {
  python3 - "$STATUS_FILE" "$CHECKS_TSV" "$WARNINGS_FILE" "$STATUS_SNAPSHOT" <<'PY'
import json
from datetime import datetime, timezone
import sys
from pathlib import Path

status_path = Path(sys.argv[1])
checks_path = Path(sys.argv[2])
warnings_path = Path(sys.argv[3])
tools_snapshot_path = Path(sys.argv[4])

checks = []
with open(checks_path, "r", encoding="utf-8") as handle:
    lines = [line.rstrip("\n") for line in handle][1:]
    for line in lines:
        if not line:
            continue
        name, status, message = line.split("\t", 2)
        checks.append({"name": name, "status": status, "message": message})

warnings = []
if warnings_path.exists():
    with open(warnings_path, "r", encoding="utf-8") as handle:
        for raw in handle.readlines()[1:]:
            raw = raw.strip()
            if not raw:
                continue
            tool, _, message = raw.partition("\t")
            warnings.append({"tool": tool, "message": message})
try:
    tools_payload = json.loads(tools_snapshot_path.read_text())
except FileNotFoundError:
    tools_payload = None

summary = {}
for check in checks:
    summary[check["status"]] = summary.get(check["status"], 0) + 1

state = "completed"
if any(check["status"] == "fail" for check in checks):
    state = "failed"
elif any(check["status"] in {"warning", "skip"} for check in checks) or warnings:
    state = "needs_attention"

extra = {
    "checks_summary": summary,
}
if tools_payload:
    extra["tools_status"] = tools_payload
    warnings.extend(tools_payload.get("warnings", []))

payload = {
    "$schema": "../status.schema.json",
    "state": state,
    "checks": checks,
    "artifacts": [
        "automation/stage01/report.md",
        "automation/stage01/created_files.txt",
    ],
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": [],
    "extra": extra,
}

status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
PY
}

update_status

log "Self-check completed"
