#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
STATUS_JSON="$SCRIPT_DIR/status.json"
SUMMARY_JSON="$SCRIPT_DIR/summary.json"
ROLE_SUMMARY_JSON="$SCRIPT_DIR/roles_summary.json"
REPORT_MD="$SCRIPT_DIR/report.md"
ROLE_DOC="$REPO_ROOT/docs/security/roles.md"
POLICY_DOC="$REPO_ROOT/docs/security/policies.md"
DATABASE_URL=${DATABASE_URL:-"sqlite:///$REPO_ROOT/backend/data/app.db"}

log() {
  printf '[stage06] %s\n' "$1"
}

log "Ensuring backend data directory exists"
mkdir -p "$REPO_ROOT/backend/data" "$REPO_ROOT/backend/var"

log "Running database migrations"
(
  cd "$REPO_ROOT/backend"
  PYTHONPATH="$REPO_ROOT/backend" DATABASE_URL="$DATABASE_URL" alembic upgrade head
)

log "Synchronising role definitions"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$DATABASE_URL" "$ROLE_SUMMARY_JSON" "$ROLE_DOC"
import json
import sys
from pathlib import Path

from app.auth.management import render_roles_markdown, sync_roles

database_url = sys.argv[1]
summary_path = Path(sys.argv[2])
role_doc = Path(sys.argv[3])

summaries = sync_roles(database_url)
render_roles_markdown(role_doc, summaries)
summary_path.write_text(json.dumps({"roles": summaries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Compiling stage summary"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$ROLE_SUMMARY_JSON" "$POLICY_DOC"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

summary_path = Path(sys.argv[1])
role_summary_path = Path(sys.argv[2])
policy_path = Path(sys.argv[3])

def safe_relative(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())

role_summary = {}
if role_summary_path.exists():
    role_summary = json.loads(role_summary_path.read_text(encoding="utf-8"))

def policy_checklist() -> list[str]:
    if not policy_path.exists():
        return []
    lines = policy_path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip().startswith("- [x]")]

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "roles": role_summary.get("roles", []),
    "policy_doc": safe_relative(policy_path),
    "checklist": policy_checklist(),
}
summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Updating stage report"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$SUMMARY_JSON" "$REPORT_MD" "$ROLE_DOC" "$POLICY_DOC"
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
report_path = Path(sys.argv[2])
role_doc = Path(sys.argv[3])
policy_doc = Path(sys.argv[4])

summary = json.loads(summary_path.read_text(encoding="utf-8"))
roles = summary.get("roles", [])

def safe_relative(path: Path) -> str:
    if not path.exists():
        return str(path)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())

policy_link = safe_relative(policy_doc)
role_link = safe_relative(role_doc)

lines = [
    "# Stage 06 Report",
    "",
    "## Summary",
    "- Authentication module implemented with JWT, refresh, MFA, and audit trail.",
    f"- Role definitions synchronised ({len(roles)} roles).",
    f"- Security policies documented in `{policy_link}`." if policy_doc.exists() else "- Security policies pending.",
    "",
    "## Role Matrix",
    f"- See `{role_link}` for full table.",
    "",
    "## Checklist",
]
checklist = summary.get("checklist", [])
if checklist:
    lines.extend(checklist)
else:
    lines.append("- [ ] Security checklist pending update")
lines.extend([
    "",
    "## Next Steps",
    "- Run `make stage06-verify` to execute tests and security checks.",
])
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "Writing stage status"
PYTHONPATH="$REPO_ROOT/backend" "$PYTHON_BIN" - <<'PY' "$STATUS_JSON" "$SUMMARY_JSON" "$ROLE_DOC" "$POLICY_DOC"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
summary_path = Path(sys.argv[2])
role_doc = Path(sys.argv[3])
policy_doc = Path(sys.argv[4])

summary = json.loads(summary_path.read_text(encoding="utf-8"))
now = datetime.now(timezone.utc).isoformat()


def safe_relative(path: Path) -> str:
    if not path.exists():
        return str(path)
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path.resolve())

payload = {
    "$schema": "../status.schema.json",
    "state": "running",
    "checks": [
        {
            "name": "alembic",
            "status": "ok",
            "message": "alembic upgrade head",
        },
        {
            "name": "roles-sync",
            "status": "ok",
            "message": "default roles synchronised",
            "path": safe_relative(role_doc) if role_doc.exists() else "",
        },
    ],
    "artifacts": [
        safe_relative(role_doc) if role_doc.exists() else "docs/security/roles.md",
        safe_relative(policy_doc) if policy_doc.exists() else "docs/security/policies.md",
        "automation/stage06/report.md",
        "automation/stage06/summary.json",
    ],
    "last_run": now,
    "warnings": [],
    "notes": ["run.sh executed"],
    "extra": {
        "roles": summary.get("roles", []),
        "policy_doc": safe_relative(policy_doc) if policy_doc.exists() else None,
    },
}
status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if command -v node >/dev/null 2>&1; then
  log "Ensuring Playwright dependencies"
  (
    cd "$REPO_ROOT/frontend"
    node scripts/install_playwright.mjs
  ) || log "Playwright dependency installation failed"
else
  log "Node.js not available; skipping Playwright dependency installation"
fi

log "Stage 06 preparation complete"
