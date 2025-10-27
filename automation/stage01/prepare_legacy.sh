#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
LEGACY_DIR="$REPO_ROOT/legacy"

mkdir -p "$LEGACY_DIR"

MARKER="$LEGACY_DIR/.migration_applied"

PHP_PATHS=(
  "src"
  "db"
  "composer.json"
  "composer.lock"
  "phinx.php"
  "migrate.sh"
  "php-fpm.conf"
  "Dockerfile"
  "docker-compose.yml"
  "app.json"
)

move_path() {
  local rel="$1"
  local src="$REPO_ROOT/$rel"
  local dest="$LEGACY_DIR/$rel"
  if [[ -e "$dest" ]]; then
    printf '✔ %s already in legacy\n' "$rel"
    return
  fi
  if [[ -e "$src" ]]; then
    mkdir -p "$(dirname "$dest")"
    printf '→ Moving %s to legacy/\n' "$rel"
    mv "$src" "$dest"
  else
    printf '⚠ %s not found in repository root\n' "$rel"
  fi
}

for item in "${PHP_PATHS[@]}"; do
  move_path "$item"
done

touch "$MARKER"
printf 'Legacy migration marker written to %s\n' "$MARKER"
