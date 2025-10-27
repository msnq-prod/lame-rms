#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
STATUS_FILE="$SCRIPT_DIR/status.json"
INVENTORY_DIR="$REPO_ROOT/docs/inventory"
BACKLOG_DIR="$REPO_ROOT/docs/backlog"
REPORT_PATH="$SCRIPT_DIR/report.md"
ARTIFACT_DIR="$SCRIPT_DIR/artifacts"
mkdir -p "$ARTIFACT_DIR"

log() {
  printf '[stage02:self-check] %s\n' "$1"
}

log "Ensuring optional tooling availability"
export STATUS_FILE
"$REPO_ROOT/automation/bin/ensure_tools.sh" >"$ARTIFACT_DIR/ensure_tools.log" 2>&1 || true

log "Running validation suite"
python3 - <<'PY' "$STATUS_FILE" "$REPO_ROOT" "$INVENTORY_DIR" "$BACKLOG_DIR" "$REPORT_PATH"
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

STATUS_PATH = Path(sys.argv[1])
REPO_ROOT = Path(sys.argv[2])
INVENTORY_DIR = Path(sys.argv[3])
BACKLOG_DIR = Path(sys.argv[4])
REPORT_PATH = Path(sys.argv[5])
BACKLOG_YAML = BACKLOG_DIR / "migration_backlog.yaml"
BACKLOG_JSON = BACKLOG_DIR / "migration_backlog.json"
FILES_JSON = INVENTORY_DIR / "files.json"
FILES_CSV = INVENTORY_DIR / "files.csv"
CRON_MD = INVENTORY_DIR / "cron.md"
METRICS_MD = INVENTORY_DIR / "metrics.md"
STRUCTURE_MMD = INVENTORY_DIR / "structure.mmd"
API_MMD = INVENTORY_DIR / "api_surface.mmd"
OPENAPI_JSON = INVENTORY_DIR / "api/openapi.json"
API_CSV = INVENTORY_DIR / "api/endpoints.csv"
API_SUMMARY = INVENTORY_DIR / "api/summary.md"
REPORT_FILE = REPORT_PATH

EXPECTED_ARTIFACTS = [
    FILES_JSON,
    FILES_CSV,
    INVENTORY_DIR / "files.md",
    METRICS_MD,
    CRON_MD,
    STRUCTURE_MMD,
    API_MMD,
    OPENAPI_JSON,
    API_CSV,
    API_SUMMARY,
    BACKLOG_YAML,
    BACKLOG_JSON,
    REPORT_FILE,
]

ALLOWED_SEVERITY = {"critical", "high", "medium", "low"}

def load_status() -> dict:
    if STATUS_PATH.exists():
        try:
            return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {
        "$schema": "../status.schema.json",
        "state": "pending",
        "checks": [],
        "artifacts": [],
        "last_run": None,
        "warnings": [],
        "notes": [],
        "extra": {},
    }


def add_check(checks: list, name: str, status: str, message: str, path: Path | None = None) -> None:
    payload = {
        "name": name,
        "status": status,
        "message": message.replace("\t", " "),
    }
    if path is not None:
        payload["path"] = str(path.as_posix())
    checks.append(payload)


def add_warning(warnings: list, tool: str, message: str) -> None:
    warnings.append({"tool": tool, "message": message})


def check_artifacts() -> tuple[str, str]:
    missing = [p for p in EXPECTED_ARTIFACTS if not p.exists()]
    if missing:
        return "fail", "Missing artifacts: " + ", ".join(str(p.relative_to(REPO_ROOT)) for p in missing)
    return "ok", f"{len(EXPECTED_ARTIFACTS)} artifacts present"


def check_file_counts() -> tuple[str, str]:
    if not FILES_JSON.exists():
        return "fail", "docs/inventory/files.json missing"
    data = json.loads(FILES_JSON.read_text(encoding="utf-8"))
    reported = len(data.get("files", []))
    total = 0
    missing_sources: list[str] = []
    for source in data.get("sources", []):
        rel = source.get("path", "")
        if not rel:
            continue
        candidate = (REPO_ROOT / rel).resolve()
        if not candidate.exists():
            missing_sources.append(rel)
            continue
        total += sum(1 for item in candidate.rglob("*") if item.is_file())
    message_parts = [f"reported={reported}", f"actual={total}"]
    if missing_sources:
        message_parts.append("missing=" + ",".join(missing_sources))
    status = "ok" if reported == total and not missing_sources else "fail"
    return status, ", ".join(message_parts)


def check_json_files() -> tuple[str, str]:
    files = [p for p in [FILES_JSON, OPENAPI_JSON, BACKLOG_JSON] if p.exists()]
    missing = [p for p in [FILES_JSON, OPENAPI_JSON, BACKLOG_JSON] if not p.exists()]
    if missing:
        return "fail", "Missing JSON files: " + ", ".join(str(p.relative_to(REPO_ROOT)) for p in missing)
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return "fail", f"{path.relative_to(REPO_ROOT)} invalid JSON: {exc}"
    return "ok", f"Validated {len(files)} JSON files"


def check_yaml_file() -> tuple[str, str]:
    if not BACKLOG_YAML.exists():
        return "fail", "docs/backlog/migration_backlog.yaml missing"
    try:
        yaml.safe_load(BACKLOG_YAML.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # noqa: BLE001
        return "fail", f"docs/backlog/migration_backlog.yaml invalid YAML: {exc}"
    return "ok", "Validated backlog YAML"


def check_csv_files() -> tuple[str, str]:
    targets = [p for p in [FILES_CSV, API_CSV] if p.exists()]
    missing = [p for p in [FILES_CSV, API_CSV] if not p.exists()]
    if missing:
        return "fail", "Missing CSV files: " + ", ".join(str(p.relative_to(REPO_ROOT)) for p in missing)
    for path in targets:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            try:
                headers = next(reader)
            except StopIteration:
                return "fail", f"{path.relative_to(REPO_ROOT)} empty"
            for row in reader:
                if len(row) != len(headers):
                    return "fail", f"{path.relative_to(REPO_ROOT)} inconsistent columns"
    return "ok", f"Validated {len(targets)} CSV files"


def check_diagrams() -> tuple[str, str]:
    diagrams = [p for p in [STRUCTURE_MMD, API_MMD] if p.exists()]
    missing = [p for p in [STRUCTURE_MMD, API_MMD] if not p.exists()]
    if missing:
        return "fail", "Missing diagrams: " + ", ".join(str(p.relative_to(REPO_ROOT)) for p in missing)
    empty = [p for p in diagrams if not p.read_text(encoding="utf-8").strip()]
    if empty:
        return "fail", "Empty diagrams: " + ", ".join(str(p.relative_to(REPO_ROOT)) for p in empty)
    return "ok", "Structure and API diagrams present"


def check_severity() -> tuple[str, str]:
    if not BACKLOG_JSON.exists():
        return "fail", "docs/backlog/migration_backlog.json missing"
    payload = json.loads(BACKLOG_JSON.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    invalid = []
    for item in items:
        severity = (item.get("risk") or {}).get("severity")
        if severity not in ALLOWED_SEVERITY:
            invalid.append(item.get("id", "<unknown>"))
    if invalid:
        return "fail", "Invalid severity in: " + ", ".join(invalid)
    return "ok", f"{len(items)} backlog items with severity"


def run_yamllint(warnings: list) -> tuple[str, str]:
    if not BACKLOG_YAML.exists():
        return "fail", "docs/backlog/migration_backlog.yaml missing"
    command = [
        "yamllint",
        "-d",
        "{extends: default, rules: {line-length: disable}}",
        str(BACKLOG_YAML),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        add_warning(warnings, "yamllint", "yamllint command unavailable")
        return "warning", "yamllint not installed"
    if result.returncode == 0:
        return "ok", "yamllint passed"
    output = (result.stdout + result.stderr).strip().replace("\n", " ")
    return "fail", output or "yamllint failed"


def compute_diff_summary() -> dict:
    command = [
        "git",
        "-C",
        str(REPO_ROOT),
        "diff",
        "--numstat",
        "--",
        "docs/inventory",
        "docs/backlog",
        "automation/stage02/report.md",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    added = 0
    deleted = 0
    files: set[str] = set()
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add, remove, path = parts
        try:
            added += int(add)
        except ValueError:
            pass
        try:
            deleted += int(remove)
        except ValueError:
            pass
        files.add(path)
    return {
        "files": sorted(files),
        "total_additions": added,
        "total_deletions": deleted,
    }


status = load_status()
checks = list(status.get("checks", []))
warnings = list(status.get("warnings", []))

artifact_status, artifact_msg = check_artifacts()
add_check(checks, "artifacts", artifact_status, artifact_msg)

file_status, file_msg = check_file_counts()
add_check(checks, "file-count", file_status, file_msg, path=FILES_JSON.relative_to(REPO_ROOT) if FILES_JSON.exists() else None)

json_status, json_msg = check_json_files()
add_check(checks, "json-validate", json_status, json_msg)

csv_status, csv_msg = check_csv_files()
add_check(checks, "csv-validate", csv_status, csv_msg)

yaml_status, yaml_msg = check_yaml_file()
add_check(checks, "yaml-validate", yaml_status, yaml_msg, path=BACKLOG_YAML.relative_to(REPO_ROOT) if BACKLOG_YAML.exists() else None)

diagram_status, diagram_msg = check_diagrams()
add_check(checks, "diagrams", diagram_status, diagram_msg)

severity_status, severity_msg = check_severity()
add_check(checks, "risk-severity", severity_status, severity_msg)

yamllint_status, yamllint_msg = run_yamllint(warnings)
add_check(checks, "yamllint", yamllint_status, yamllint_msg, path=BACKLOG_YAML.relative_to(REPO_ROOT) if BACKLOG_YAML.exists() else None)

status["checks"] = checks
status["warnings"] = warnings
status["artifacts"] = [str(path.relative_to(REPO_ROOT)) for path in EXPECTED_ARTIFACTS if path.exists()]
status["last_run"] = datetime.now(timezone.utc).isoformat()
status.setdefault("notes", []).append("self_check.sh executed")
status.setdefault("extra", {})["diff_summary"] = compute_diff_summary()

has_fail = any(item.get("status") == "fail" for item in checks)
has_warning = any(item.get("status") == "warning" for item in checks) or warnings
if has_fail:
    status["state"] = "failed"
elif has_warning:
    status["state"] = "needs_attention"
else:
    status["state"] = "completed"

STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("Checks recorded:")
for item in checks:
    print(f" - {item['name']}: {item['status']} ({item['message']})")
if warnings:
    print("Warnings:")
    for warn in warnings:
        print(f" - {warn['tool']}: {warn['message']}")
print("State:", status["state"])
PY
