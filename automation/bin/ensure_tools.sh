#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPO_ROOT=$(cd "$ROOT_DIR/.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
TOOLS_DIR="$ROOT_DIR/bin/tools"

mkdir -p "$TOOLS_DIR"

if [[ -z "${ENSURE_TOOLS_ORIG_PATH:-}" ]]; then
  export ENSURE_TOOLS_ORIG_PATH="$PATH"
fi

case ":$PATH:" in
  *:"$TOOLS_DIR":*) ;;
  *) export PATH="$TOOLS_DIR:$PATH" ;;
esac

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
    if "$cmd" --version >/dev/null 2>&1; then
      FOUND_PATH=$(command -v "$cmd")
      return 0
    fi
  fi
  return 1
}

ASDF_AVAILABLE=false
NPM_AVAILABLE=false
NPX_AVAILABLE=false

SYSTEM_OS=$(uname -s | tr '[:upper:]' '[:lower:]')
SYSTEM_ARCH=$(uname -m | tr '[:upper:]' '[:lower:]')

normalize_arch() {
  local arch="$1"
  case "$arch" in
    x86_64|amd64) printf 'amd64' ;;
    arm64|aarch64) printf 'arm64' ;;
    *) printf '%s' "$arch" ;;
  esac
}

normalize_os() {
  local os="$1"
  case "$os" in
    linux|darwin) printf '%s' "$os" ;;
    *) printf '%s' "$os" ;;
  esac
}

download_and_extract() {
  local url="$1"
  local archive_path="$2"
  local extract_dir="$3"
  if ! curl -fsSL "$url" -o "$archive_path"; then
    INSTALL_RESULT_MESSAGE="failed to download $url"
    return 1
  fi

  mkdir -p "$extract_dir"

  case "$archive_path" in
    *.tar.gz|*.tgz)
      if ! tar -xzf "$archive_path" -C "$extract_dir"; then
        INSTALL_RESULT_MESSAGE="failed to extract archive $archive_path"
        return 1
      fi
      ;;
    *.zip)
      if ! unzip -qo "$archive_path" -d "$extract_dir"; then
        INSTALL_RESULT_MESSAGE="failed to unzip archive $archive_path"
        return 1
      fi
      ;;
    *)
      INSTALL_RESULT_MESSAGE="unsupported archive format for $archive_path"
      return 1
      ;;
  esac

  return 0
}

install_release_binary() {
  local binary_name="$1"
  local url="$2"
  local extracted_path="$3"
  local destination="$TOOLS_DIR/${binary_name}-bin"

  local tmpdir
  tmpdir=$(mktemp -d)
  local archive_name
  archive_name=$(basename "$url")
  local archive="$tmpdir/$archive_name"

  if ! download_and_extract "$url" "$archive" "$tmpdir/extracted"; then
    rm -rf "$tmpdir"
    return 1
  fi

  local source_path="$tmpdir/extracted/$extracted_path"
  if [[ ! -f "$source_path" ]]; then
    INSTALL_RESULT_MESSAGE="binary not found at $source_path"
    rm -rf "$tmpdir"
    return 1
  fi

  if ! mv -f "$source_path" "$destination"; then
    INSTALL_RESULT_MESSAGE="failed to move binary to $destination"
    rm -rf "$tmpdir"
    return 1
  fi

  chmod +x "$destination"
  rm -rf "$tmpdir"

  INSTALL_METHOD="download"
  INSTALL_RESULT_MESSAGE="downloaded release from $url"
  return 0
}

ensure_dependency() {
  local name="$1"
  local flag_var="$2"
  local binary_name="${3:-$1}"

  local status="warning"
  local message="$name not available"
  local path=""

  if command -v "$binary_name" >/dev/null 2>&1; then
    status="ok"
    message="found"
    path=$(command -v "$binary_name")
    printf -v "$flag_var" '%s' "true"
    log "✔ $name available at $path"
  else
    printf -v "$flag_var" '%s' "false"
    log "⚠ $name not found"
  fi

  local delim=$'\t'
  RESULT_LINES+=("${name}${delim}${status}${delim}${message}${delim}${path}")
}

check_act() {
  check_command act
}

check_k6() {
  check_command k6
}

check_schemathesis() {
  check_command schemathesis
}

check_terraform() {
  check_command terraform
}

check_helm() {
  check_command helm
}

check_playwright() {
  check_command playwright
}

check_bandit() {
  check_command bandit
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

install_act_release() {
  local os_capitalized="${SYSTEM_OS^}"
  local arch_suffix
  case "$SYSTEM_ARCH" in
    x86_64|amd64) arch_suffix="x86_64" ;;
    arm64|aarch64) arch_suffix="arm64" ;;
    *)
      INSTALL_RESULT_MESSAGE="unsupported architecture $SYSTEM_ARCH"
      return 1
      ;;
  esac
  local version="${ACT_VERSION:-v0.2.59}"
  local url="https://github.com/nektos/act/releases/download/${version}/act_${os_capitalized}_${arch_suffix}.tar.gz"
  install_release_binary "act" "$url" "act"
}

install_act() {
  if [[ "$ASDF_AVAILABLE" == "true" ]]; then
    install_tool_via_asdf act
  else
    install_act_release
  fi
}

install_k6() {
  if [[ "$ASDF_AVAILABLE" == "true" ]]; then
    install_tool_via_asdf k6
    return $?
  fi

  local os_normalized
  os_normalized=$(normalize_os "$SYSTEM_OS")
  local arch_normalized
  arch_normalized=$(normalize_arch "$SYSTEM_ARCH")
  case "$os_normalized" in
    linux|darwin) ;;
    *)
      INSTALL_RESULT_MESSAGE="unsupported operating system $SYSTEM_OS"
      return 1
      ;;
  esac

  local version="${K6_VERSION:-v0.45.0}"
  local archive_name="k6-${version}-${os_normalized}-${arch_normalized}.tar.gz"
  local url="https://github.com/grafana/k6/releases/download/${version}/${archive_name}"
  local extracted="k6-${version}-${os_normalized}-${arch_normalized}/k6"
  install_release_binary "k6" "$url" "$extracted"
}

install_schemathesis() {
  INSTALL_RESULT_MESSAGE=""

  if command -v pipx >/dev/null 2>&1; then
    INSTALL_METHOD="pipx"
    if pipx install schemathesis >/dev/null 2>&1 || pipx upgrade schemathesis >/dev/null 2>&1; then
      INSTALL_RESULT_MESSAGE="installed via pipx"
      return 0
    fi
  fi

  INSTALL_METHOD="pip"

  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    INSTALL_RESULT_MESSAGE="python interpreter not available"
    return 1
  fi

  if "$PYTHON_BIN" -m pip install --user --quiet schemathesis >/dev/null 2>&1; then
    INSTALL_RESULT_MESSAGE="installed via pip --user"
    return 0
  fi

  INSTALL_RESULT_MESSAGE="pip install --user schemathesis failed"
  return 1
}

install_terraform() {
  if [[ "$ASDF_AVAILABLE" == "true" ]]; then
    install_tool_via_asdf terraform
    return $?
  fi

  local os_normalized
  os_normalized=$(normalize_os "$SYSTEM_OS")
  local arch_normalized
  arch_normalized=$(normalize_arch "$SYSTEM_ARCH")

  if [[ "$os_normalized" != "linux" && "$os_normalized" != "darwin" ]]; then
    INSTALL_RESULT_MESSAGE="unsupported operating system $SYSTEM_OS"
    return 1
  fi

  local version="${TERRAFORM_VERSION:-1.6.6}"
  local url="https://releases.hashicorp.com/terraform/${version}/terraform_${version}_${os_normalized}_${arch_normalized}.zip"
  install_release_binary "terraform" "$url" "terraform"
}

install_helm() {
  if [[ "$ASDF_AVAILABLE" == "true" ]]; then
    install_tool_via_asdf helm
    return $?
  fi

  local os_normalized
  os_normalized=$(normalize_os "$SYSTEM_OS")
  local arch_normalized
  arch_normalized=$(normalize_arch "$SYSTEM_ARCH")
  if [[ "$os_normalized" != "linux" && "$os_normalized" != "darwin" ]]; then
    INSTALL_RESULT_MESSAGE="unsupported operating system $SYSTEM_OS"
    return 1
  fi

  local version="${HELM_VERSION:-v3.14.4}"
  local url="https://get.helm.sh/helm-${version}-${os_normalized}-${arch_normalized}.tar.gz"
  local extracted="${os_normalized}-${arch_normalized}/helm"
  install_release_binary "helm" "$url" "$extracted"
}

install_playwright() {
  INSTALL_METHOD="npx"
  INSTALL_RESULT_MESSAGE=""

  if [[ "$NPX_AVAILABLE" != "true" ]]; then
    INSTALL_RESULT_MESSAGE="npx not available"
    return 1
  fi

  if npx --yes playwright install >/dev/null 2>&1; then
    INSTALL_RESULT_MESSAGE="installed via npx"
    return 0
  fi

  INSTALL_RESULT_MESSAGE="npx playwright install failed"
  return 1
}

install_bandit() {
  INSTALL_RESULT_MESSAGE=""

  if command -v pipx >/dev/null 2>&1; then
    INSTALL_METHOD="pipx"
    if pipx install bandit >/dev/null 2>&1 || pipx upgrade bandit >/dev/null 2>&1; then
      INSTALL_RESULT_MESSAGE="installed via pipx"
      return 0
    fi
  fi

  INSTALL_METHOD="pip"

  if command -v python >/dev/null 2>&1; then
    if python -m pip install --user bandit >/dev/null 2>&1; then
      INSTALL_RESULT_MESSAGE="installed via python -m pip --user"
      return 0
    fi
  fi

  if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    if "$PYTHON_BIN" -m pip install --user bandit >/dev/null 2>&1; then
      INSTALL_RESULT_MESSAGE="installed via ${PYTHON_BIN} -m pip --user"
      return 0
    fi
  else
    INSTALL_RESULT_MESSAGE="python interpreter not available"
    return 1
  fi

  INSTALL_RESULT_MESSAGE="python -m pip install --user bandit failed"
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

ensure_dependency "asdf" ASDF_AVAILABLE "asdf"
ensure_dependency "npm" NPM_AVAILABLE "npm"
ensure_dependency "npx" NPX_AVAILABLE "npx"

ensure_tool "act" check_act install_act
ensure_tool "k6" check_k6 install_k6
ensure_tool "schemathesis" check_schemathesis install_schemathesis
ensure_tool "bandit" check_bandit install_bandit
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

warnings = [
    {"tool": row["name"], "message": row["message"]}
    for row in payload_rows
    if row.get("status") not in {"ok", "installed"}
]

summary = {
    "total": len(payload_rows),
    "ok": sum(1 for row in payload_rows if row.get("status") == "ok"),
    "installed": sum(1 for row in payload_rows if row.get("status") == "installed"),
    "warnings": sum(1 for row in payload_rows if row.get("status") not in {"ok", "installed"}),
}

payload = {
    "state": "completed" if not warnings else "needs_attention",
    "checks": payload_rows,
    "artifacts": [],
    "last_run": datetime.now(timezone.utc).isoformat(),
    "warnings": warnings,
    "notes": [],
    "extra": {
        "tools_summary": summary,
    },
}

with open(status_file, "w", encoding="utf-8") as fp:
    json.dump(payload, fp, ensure_ascii=False, indent=2)
    fp.write("\n")
PY

if [[ "$KEEP_TMP" != "1" ]]; then
  rm -f "$tmpfile"
else
  log "Debug TSV preserved at $tmpfile"
fi
trap - EXIT

log "Status written to $STATUS_FILE"
