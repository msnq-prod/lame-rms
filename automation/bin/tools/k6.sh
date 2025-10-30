#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_common.sh"

run_wrapped_tool "k6" "$SCRIPT_DIR" \
  "$SCRIPT_DIR/k6-bin" \
  "$HOME/.local/bin/k6" \
  -- \
  "$@"
