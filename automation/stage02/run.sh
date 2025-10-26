#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

INVENTORY_DIR="$REPO_ROOT/docs/inventory"
BACKLOG_DIR="$REPO_ROOT/docs/backlog"
API_DIR="$INVENTORY_DIR/api"

mkdir -p "$INVENTORY_DIR" "$BACKLOG_DIR" "$API_DIR"

python3 "$SCRIPT_DIR/generate_inventory.py" \
  --repo-root "$REPO_ROOT" \
  --inventory-dir "$INVENTORY_DIR" \
  --backlog-dir "$BACKLOG_DIR" \
  --report-path "$SCRIPT_DIR/report.md"

echo "Stage 02 inventory generated"
