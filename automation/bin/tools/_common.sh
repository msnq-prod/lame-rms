#!/usr/bin/env bash

set -euo pipefail

resolve_tool_binary() {
  local cmd="$1"
  shift
  local script_dir="$1"
  shift
  local -a candidates=("$@")

  for candidate in "${candidates[@]}"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  local search_path="${ENSURE_TOOLS_ORIG_PATH:-$PATH}"
  local filtered=""

  IFS=':' read -ra path_parts <<<"$search_path"
  for part in "${path_parts[@]}"; do
    [[ -z "$part" ]] && continue
    if [[ "$part" == "$script_dir" ]]; then
      continue
    fi
    if [[ -z "$filtered" ]]; then
      filtered="$part"
    else
      filtered="$filtered:$part"
    fi
  done

  if [[ -z "$filtered" ]]; then
    filtered="$search_path"
  fi

  local found
  found=$(PATH="$filtered" command -v "$cmd" 2>/dev/null || true)
  if [[ -n "$found" && "$found" != "$script_dir/$cmd" && "$found" != "$script_dir/$cmd.sh" ]]; then
    printf '%s\n' "$found"
    return 0
  fi

  return 1
}

run_wrapped_tool() {
  local cmd="$1"
  shift
  local script_dir="$1"
  shift

  local -a candidates=()
  while (($#)); do
    if [[ "$1" == "--" ]]; then
      shift
      break
    fi
    candidates+=("$1")
    shift
  done

  local -a args=("$@")

  local binary
  if ! binary=$(resolve_tool_binary "$cmd" "$script_dir" "${candidates[@]}"); then
    printf 'Error: %s is not installed. Please run automation/bin/ensure_tools.sh.\n' "$cmd" >&2
    exit 127
  fi

  exec "$binary" "${args[@]}"
}
