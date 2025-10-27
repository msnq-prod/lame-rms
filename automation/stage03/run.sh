#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PHINX_BIN="$REPO_ROOT/vendor/bin/phinx"
PHINX_CONFIG="$REPO_ROOT/phinx.php"
SCHEMA_FILE="$REPO_ROOT/db/schema.php"
PHINX_ENVIRONMENT="${PHINX_ENVIRONMENT:-${PHINX_ENV:-production}}"

refresh_schema() {
  if [[ "${SKIP_PHINX_SCHEMA_DUMP:-0}" == "1" ]]; then
    return 0
  fi
  if [[ ! -x "$PHINX_BIN" ]]; then
    if [[ -f "$PHINX_BIN" ]]; then
      chmod +x "$PHINX_BIN" 2>/dev/null || true
    fi
  fi
  if [[ ! -x "$PHINX_BIN" ]]; then
    echo "[stage03] Skipping Phinx schema dump: $PHINX_BIN not found." >&2
    return 1
  fi
  if ! command -v php >/dev/null 2>&1; then
    echo "[stage03] Skipping Phinx schema dump: php command not available." >&2
    return 1
  fi
  if [[ ! -f "$PHINX_CONFIG" ]]; then
    echo "[stage03] Skipping Phinx schema dump: phinx.php not found." >&2
    return 1
  fi
  echo "[stage03] Refreshing schema via Phinx (environment: $PHINX_ENVIRONMENT)"
  if php "$PHINX_BIN" schema:dump --configuration="$PHINX_CONFIG" --environment="$PHINX_ENVIRONMENT" >/dev/null 2>&1; then
    echo "[stage03] Schema dumped to $SCHEMA_FILE"
    return 0
  else
    echo "[stage03] Warning: Phinx schema dump failed, continuing with existing schema." >&2
    return 1
  fi
}

refresh_schema || true

if [[ ! -f "$SCHEMA_FILE" ]]; then
  echo "[stage03] Error: schema file $SCHEMA_FILE not found." >&2
  echo "[stage03] Provide a schema using vendor/bin/phinx schema:dump or set SKIP_PHINX_SCHEMA_DUMP=1 with an existing file." >&2
  exit 1
fi

python3 "$SCRIPT_DIR/generate_assets.py" "$@"
echo "Stage 03 assets generated"
