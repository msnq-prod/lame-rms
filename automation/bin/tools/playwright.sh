#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_common.sh"

local_binary="${SCRIPT_DIR}/playwright-bin"
if [[ -x "$local_binary" ]]; then
  exec "$local_binary" "$@"
fi

if resolved=$(resolve_tool_binary "playwright" "$SCRIPT_DIR" "$HOME/.local/bin/playwright"); then
  exec "$resolved" "$@"
fi

if command -v npx >/dev/null 2>&1; then
  exec npx --yes playwright "$@"
fi

printf 'Error: playwright is not available. Please run automation/bin/ensure_tools.sh.\n' >&2
exit 127
