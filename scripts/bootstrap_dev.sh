#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

copy_if_missing() {
  local source="$1"
  local target="$2"
  if [[ -f "$source" && ! -f "$target" ]]; then
    printf '[bootstrap-dev] Copying %s -> %s\n' "${source#$REPO_ROOT/}" "${target#$REPO_ROOT/}"
    cp "$source" "$target"
  fi
}

copy_if_missing "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
copy_if_missing "$REPO_ROOT/backend/.env.example" "$REPO_ROOT/backend/.env"
copy_if_missing "$REPO_ROOT/frontend/.env.example" "$REPO_ROOT/frontend/.env"

if command -v python3 >/dev/null 2>&1; then
  VENV_DIR="$REPO_ROOT/backend/.venv"
  if [[ ! -d "$VENV_DIR" ]]; then
    printf '[bootstrap-dev] Creating backend virtualenv at %s\n' "${VENV_DIR#$REPO_ROOT/}"
    python3 -m venv "$VENV_DIR"
  else
    printf '[bootstrap-dev] Backend virtualenv already exists\n'
  fi
else
  printf '[bootstrap-dev] python3 not found, skipping virtualenv creation\n'
fi

printf '[bootstrap-dev] Done\n'
