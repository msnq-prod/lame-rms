#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPO_ROOT=$(cd "$ROOT_DIR/.." && pwd)

STATUS_FILE="${STATUS_FILE:-$ROOT_DIR/status.json}"
if [[ $# -gt 0 ]]; then
  STATUS_FILE="$1"
fi

mkdir -p "$(dirname "$STATUS_FILE")"

FOUND_PATH=""
INSTALL_METHOD=""
INSTALL_RESULT_MESSAGE=""

log() {
  printf '%s\n' "$1"
}

check_command() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    FOUND_PATH=$(command -v "$cmd")
    return 0
  fi
  return 1
}

check_act() {
  check_command act
}

check_k6() {
  check_command k6
}

check_terraform() {
  check_command terraform
}

check_helm() {
  check_command helm
}

check_playwright() {
  FOUND_PATH=""
  if check_command playwright; then
    return 0
  fi
  if command -v npx >/dev/null 2>&1 && npx --yes playwright --version >/dev/null 2>&1; then
    FOUND_PATH=$(command -v npx)
    return 0
  fi
  return 1
}

install_tool_via_asdf() {
  local plugin="$1"
  INSTALL_METHOD="asdf"
  INSTALL_RESULT_MESSAGE=""

  if ! command -v asdf >/dev/null 2>&1; then
    INSTALL_RESULT_MESSAGE="asdf not available"
    return 1
  fi

  if ! asdf plugin-list | grep -Fxq "$plugin"; then
    if ! asdf plugin-add "$plugin" >/dev/null 2>&1; then
      INSTALL_RESULT_MESSAGE="failed to add asdf plugin"
      return 1
    fi
  fi

  local version_file="$REPO_ROOT/.tool-versions"
  if [[ -f "$version_file" ]] && grep -q "^$plugin " "$version_file"; then
    if ! asdf install "$plugin" >/dev/null 2>&1; then
      INSTALL_RESULT_MESSAGE="asdf install failed (check .tool-versions)"
      return 1
    fi
  else
    INSTALL_RESULT_MESSAGE="no version specified in .tool-versions"
    return 1
  fi

  asdf reshim "$plugin" >/dev/null 2>&1 || true
  INSTALL_RESULT_MESSAGE="installed via asdf"
  return 0
}

install_act() {
  install_tool_via_asdf act
}

install_k6() {
  install_tool_via_asdf k6
}

install_terraform() {
  install_tool_via_asdf terraform
}

install_helm() {
  install_tool_via_asdf helm
}

install_playwright() {
  INSTALL_METHOD="npm"
  INSTALL_RESULT_MESSAGE=""

  if ! command -v npm >/dev/null 2>&1; then
    INSTALL_RESULT_MESSAGE="npm not available"
    return 1
  fi

  if npm install --global playwright >/dev/null 2>&1; then
    INSTALL_RESULT_MESSAGE="installed via npm"
    return 0
  fi

  INSTALL_RESULT_MESSAGE="npm install -g playwright failed"
  return 1
}

RESULT_LINES=()

ensure_tool() {
  local name="$1"
  local check_func="$2"
  local install_func="$3"

  local status=""
  local message=""
  local path=""

  FOUND_PATH=""
  INSTALL_METHOD=""
  INSTALL_RESULT_MESSAGE=""
  if "$check_func"; then
    status="ok"
    path="$FOUND_PATH"
    message="found"
    log "✔ $name available at ${path:-PATH}"
  else
    if "$install_func"; then
      FOUND_PATH=""
      if "$check_func"; then
        status="installed"
        path="$FOUND_PATH"
        message="${INSTALL_RESULT_MESSAGE:-installed}"
        log "➕ $name installed via ${INSTALL_METHOD}"
      else
        status="warning"
        message="${INSTALL_RESULT_MESSAGE:-installation attempt failed}"
        log "⚠ $name installation attempted via ${INSTALL_METHOD:-unknown} but command still missing"
      fi
    else
      status="warning"
      message="${INSTALL_RESULT_MESSAGE:-not installed}"
      log "⚠ $name not installed"
    fi
  fi

  path="${path:-}" 
  message=${message//$'\t'/ }
  local delim=$'\t'
  RESULT_LINES+=("${name}${delim}${status}${delim}${message}${delim}${path}")
}

ensure_tool "act" check_act install_act
ensure_tool "k6" check_k6 install_k6
ensure_tool "playwright" check_playwright install_playwright
ensure_tool "terraform" check_terraform install_terraform
ensure_tool "helm" check_helm install_helm

tmpfile=$(mktemp)
KEEP_TMP=${KEEP_TMP:-0}
trap '[[ "$KEEP_TMP" != "1" ]] && rm -f "$tmpfile"' EXIT
tab=$'\t'
{
  printf '%s\n' "name${tab}status${tab}message${tab}path"
  for line in "${RESULT_LINES[@]}"; do
    printf '%s\n' "$line"
  done
} >"$tmpfile"

python3 - "$STATUS_FILE" "$tmpfile" <<'PY'
import json
import sys
from datetime import datetime, timezone

status_file = sys.argv[1]
data_file = sys.argv[2]

with open(data_file, "r", encoding="utf-8") as handle:
    lines = [line.rstrip("\n") for line in handle if line.rstrip("\n")]

if lines:
    headers = lines[0].split("\t")
    payload_rows = [
        dict(zip(headers, raw.split("\t")))
        for raw in lines[1:]
    ]
else:
    payload_rows = []

payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tools": payload_rows,
}
with open(status_file, "w", encoding="utf-8") as fp:
    json.dump(payload, fp, ensure_ascii=False, indent=2)
PY

if [[ "$KEEP_TMP" != "1" ]]; then
  rm -f "$tmpfile"
else
  log "Debug TSV preserved at $tmpfile"
fi
trap - EXIT

log "Status written to $STATUS_FILE"
