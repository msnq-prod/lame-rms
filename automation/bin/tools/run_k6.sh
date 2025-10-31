#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKDIR="/workspace"
IMAGE="${K6_IMAGE:-grafana/k6:latest}"
ENGINE="${CONTAINER_ENGINE:-}"

if [[ -z "$ENGINE" ]]; then
  if command -v docker >/dev/null 2>&1; then
    ENGINE="docker"
  elif command -v podman >/dev/null 2>&1; then
    ENGINE="podman"
  elif [[ -x "$SCRIPT_DIR/podman.sh" ]]; then
    ENGINE="$SCRIPT_DIR/podman.sh"
  else
    printf 'Error: Neither docker nor podman is available to run k6 container.\n' >&2
    exit 127
  fi
fi

VOLUME_SPEC="$REPO_ROOT:$WORKDIR"
if [[ "$ENGINE" == "podman" ]]; then
  VOLUME_SPEC="$REPO_ROOT:$WORKDIR:Z"
fi

NETWORK_ARGS=()
if [[ "${DISABLE_HOST_NETWORK:-0}" != "1" ]]; then
  NETWORK_ARGS+=(--network host)
fi

USER_ARGS=()
if id -u >/dev/null 2>&1 && id -g >/dev/null 2>&1; then
  USER_ARGS+=(--user "$(id -u):$(id -g)")
fi

if [[ "$ENGINE" == "$SCRIPT_DIR/podman.sh" ]]; then
  exec "$ENGINE" run \
    --rm \
    "${NETWORK_ARGS[@]}" \
    -v "$VOLUME_SPEC" \
    -w "$WORKDIR" \
    "${USER_ARGS[@]}" \
    "$IMAGE" "$@"
else
  exec "$ENGINE" run --rm \
    "${NETWORK_ARGS[@]}" \
    -v "$VOLUME_SPEC" \
    -w "$WORKDIR" \
    "${USER_ARGS[@]}" \
    "$IMAGE" "$@"
fi
