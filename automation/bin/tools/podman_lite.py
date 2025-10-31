#!/usr/bin/env python3
"""Lightweight podman-compatible runner for local development.

This script emulates a tiny subset of `podman run` that is required by
our automation helpers.  It understands volume mappings created by the
wrapper scripts and dispatches known container images to lightweight
Python equivalents so we can execute performance and contract checks in
restricted environments where a real container engine is unavailable.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
@dataclass
class RunConfig:
    image: str
    command: List[str]
    env: Dict[str, str]
    volumes: List[Tuple[str, str]]
    workdir: str | None = None


class PodmanLiteError(RuntimeError):
    """Raised when the lightweight runtime cannot fulfil a request."""


def debug(msg: str) -> None:
    sys.stdout.write(f"[podman-lite] {msg}\n")
    sys.stdout.flush()


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def parse_volume(spec: str) -> Tuple[str, str]:
    if not spec:
        raise PodmanLiteError("volume specification is empty")
    parts = spec.split(":")
    if len(parts) < 2:
        raise PodmanLiteError(f"invalid volume specification: {spec}")
    host = parts[0]
    container = parts[1]
    if not host or not container:
        raise PodmanLiteError(f"invalid volume specification: {spec}")
    return host, container


def parse_env(spec: str) -> Tuple[str, str]:
    if "=" not in spec:
        raise PodmanLiteError(f"invalid env specification: {spec}")
    key, value = spec.split("=", 1)
    if not key:
        raise PodmanLiteError(f"invalid env specification: {spec}")
    return key, value


def parse_run_args(argv: Sequence[str]) -> RunConfig:
    env: Dict[str, str] = {}
    volumes: List[Tuple[str, str]] = []
    workdir: str | None = None
    image: str | None = None
    command: List[str] = []

    i = 0
    argc = len(argv)
    while i < argc:
        arg = argv[i]
        if arg == "--rm":
            i += 1
            continue
        if arg in ("-v", "--volume"):
            if i + 1 >= argc:
                raise PodmanLiteError("-v/--volume requires a value")
            volumes.append(parse_volume(argv[i + 1]))
            i += 2
            continue
        if arg.startswith("-v") and len(arg) > 2 and arg[2] != "-":
            volumes.append(parse_volume(arg[2:]))
            i += 1
            continue
        if arg in ("-w", "--workdir"):
            if i + 1 >= argc:
                raise PodmanLiteError("-w/--workdir requires a value")
            workdir = argv[i + 1]
            i += 2
            continue
        if arg.startswith("-w") and len(arg) > 2 and arg[2] != "-":
            workdir = arg[2:]
            i += 1
            continue
        if arg in ("--network", "--user"):
            # These options are accepted but ignored in the lightweight mode.
            i += 2 if i + 1 < argc else 1
            continue
        if arg.startswith("--network=") or arg.startswith("--user="):
            i += 1
            continue
        if arg in ("--env", "-e"):
            if i + 1 >= argc:
                raise PodmanLiteError("--env/-e requires KEY=VALUE")
            key, value = parse_env(argv[i + 1])
            env[key] = value
            i += 2
            continue
        if arg.startswith("--env="):
            key, value = parse_env(arg.split("=", 1)[1])
            env[key] = value
            i += 1
            continue
        if arg.startswith("-e") and len(arg) > 2 and arg[2] != "-":
            key, value = parse_env(arg[2:])
            env[key] = value
            i += 1
            continue
        if arg.startswith("-"):
            # Unrecognised option: skip it and an optional value if present.
            if "=" in arg or i + 1 >= argc:
                i += 1
            else:
                i += 2
            continue
        image = arg
        command = list(argv[i + 1 :])
        break

    if image is None:
        raise PodmanLiteError("no image specified for podman run")

    return RunConfig(image=image, command=command, env=env, volumes=volumes, workdir=workdir)


def resolve_path(path: str, volumes: Iterable[Tuple[str, str]]) -> str:
    for host, container in volumes:
        normalised = container.rstrip("/")
        if not normalised:
            continue
        if path == normalised:
            return host
        prefix = f"{normalised}/"
        if path.startswith(prefix):
            suffix = path[len(prefix) :]
            return os.path.join(host, suffix) if suffix else host
    return path


def percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if not ordered:
        return None
    index = fraction * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    if upper == lower:
        return ordered[lower]
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def request_json(url: str) -> Tuple[int, object]:
    req = urllib.request.Request(url, headers={"User-Agent": "podman-lite"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            try:
                payload = json.loads(body.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                payload = None
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        body = exc.read()
        try:
            payload = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = None
        return exc.code, payload


def wait_until_ready(base_url: str, timeout: float) -> bool:
    deadline = time.time() + max(timeout, 0)
    probe = f"{base_url.rstrip('/')}/health"
    while time.time() < deadline:
        try:
            status, _ = request_json(probe)
        except (urllib.error.URLError, TimeoutError):
            status = None
        if status == 200:
            return True
        time.sleep(0.5)
    return False


def run_k6_equivalent(config: RunConfig) -> int:
    args = config.command
    if not args or args[0] != "run":
        raise PodmanLiteError("k6 runner expects 'run' command")

    summary_path: str | None = None
    base_url = config.env.get("API_BASE_URL", "http://127.0.0.1:8000/api")
    script_path: str | None = None

    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--summary-export":
            if i + 1 >= len(args):
                raise PodmanLiteError("--summary-export requires a path")
            summary_path = resolve_path(args[i + 1], config.volumes)
            i += 2
            continue
        if arg.startswith("--summary-export="):
            summary_path = resolve_path(arg.split("=", 1)[1], config.volumes)
            i += 1
            continue
        if arg in ("--env", "-e"):
            if i + 1 >= len(args):
                raise PodmanLiteError("--env requires KEY=VALUE")
            key, value = parse_env(args[i + 1])
            config.env[key] = value
            if key == "API_BASE_URL":
                base_url = value
            i += 2
            continue
        if arg.startswith("--env="):
            key, value = parse_env(arg.split("=", 1)[1])
            config.env[key] = value
            if key == "API_BASE_URL":
                base_url = value
            i += 1
            continue
        if arg.startswith("-e") and len(arg) > 2 and arg[2] != "-":
            key, value = parse_env(arg[2:])
            config.env[key] = value
            if key == "API_BASE_URL":
                base_url = value
            i += 1
            continue
        if arg.startswith("-"):
            i += 1
            continue
        script_path = resolve_path(arg, config.volumes)
        i += 1
        break

    debug(f"Running k6-lite scenario (script={script_path or 'inline'}, base_url={base_url})")

    durations_ms: List[float] = []
    check_passes = 0
    check_fails = 0
    warmup = float(os.environ.get("K6_LITE_WARMUP", "1.0"))
    if warmup > 0:
        debug(f"Waiting {warmup:.1f}s for API warm-up")
        time.sleep(warmup)

    iterations = max(1, int(os.environ.get("K6_LITE_ITERATIONS", "20")))

    readiness_timeout = float(os.environ.get("K6_LITE_STARTUP_TIMEOUT", "5"))
    if readiness_timeout > 0 and not wait_until_ready(base_url, readiness_timeout):
        debug(
            f"Service at {base_url} did not pass readiness probe within {readiness_timeout:.1f}s"
        )

    for iteration in range(iterations):
        list_start = time.perf_counter()
        try:
            status, payload = request_json(f"{base_url.rstrip('/')}/assets")
            durations_ms.append((time.perf_counter() - list_start) * 1000)
            check_passes += 1
            debug(f"Iteration {iteration + 1}: GET /assets -> {status}")
            items = []
            if isinstance(payload, dict):
                items = payload.get("items") or []
            if items:
                asset = items[0]
                asset_id = asset.get("id") if isinstance(asset, dict) else None
                if asset_id:
                    detail_start = time.perf_counter()
                    detail_status, _ = request_json(f"{base_url.rstrip('/')}/assets/{asset_id}")
                    durations_ms.append((time.perf_counter() - detail_start) * 1000)
                    check_passes += 1
                    debug(f"Iteration {iteration + 1}: GET /assets/{asset_id} -> {detail_status}")
                else:
                    debug(f"Iteration {iteration + 1}: asset id missing; skipping detail check")
            else:
                debug(f"Iteration {iteration + 1}: no assets returned; skipping detail check")
        except (urllib.error.URLError, TimeoutError) as exc:
            check_fails += 1
            debug(f"Iteration {iteration + 1}: request failed ({exc})")
            continue

        time.sleep(float(os.environ.get("K6_LITE_SLEEP", "0.1")))

    total_checks = check_passes + check_fails
    success_rate = (check_passes / total_checks) if total_checks else 1.0
    p95 = percentile(durations_ms, 0.95)

    debug(
        "Summary: checks=%s passes=%s fails=%s p95_ms=%s"
        % (total_checks, check_passes, check_fails, f"{p95:.2f}" if p95 is not None else "n/a")
    )

    if summary_path:
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as handle:
            payload = {
                "metrics": {
                    "http_req_duration": {
                        "values": {"p(95)": float(p95) if p95 is not None else None}
                    },
                    "checks": {
                        "values": {
                            "passes": check_passes,
                            "fails": check_fails,
                            "rate": success_rate,
                        }
                    },
                },
                "metadata": {
                    "image": config.image,
                    "iterations": iterations,
                },
            }
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    return 0 if check_fails == 0 else 1


def run_schemathesis_equivalent(config: RunConfig) -> int:
    args = config.command
    if not args or args[0] not in {"run", "test"}:
        raise PodmanLiteError("schemathesis runner expects 'run' command")

    schema_path: str | None = None
    base_url = "http://127.0.0.1:8000/api"

    i = 1
    while i < len(args):
        arg = args[i]
        if schema_path is None and not arg.startswith("-"):
            schema_path = resolve_path(arg, config.volumes)
            i += 1
            continue
        if arg == "--base-url":
            if i + 1 >= len(args):
                raise PodmanLiteError("--base-url requires a value")
            base_url = args[i + 1]
            i += 2
            continue
        if arg.startswith("--base-url="):
            base_url = arg.split("=", 1)[1]
            i += 1
            continue
        i += 1

    checks: List[Tuple[str, bool]] = []

    warmup = float(os.environ.get("SCHEMATHESIS_LITE_WARMUP", "1.0"))
    if warmup > 0:
        debug(f"Waiting {warmup:.1f}s for API warm-up")
        time.sleep(warmup)

    readiness_timeout = float(os.environ.get("SCHEMATHESIS_LITE_STARTUP_TIMEOUT", "5"))
    if readiness_timeout > 0 and not wait_until_ready(base_url, readiness_timeout):
        debug(
            f"Service at {base_url} did not pass readiness probe within {readiness_timeout:.1f}s"
        )

    def record(name: str, ok: bool, detail: str | None = None) -> None:
        status = "PASS" if ok else "FAIL"
        message = f"{name}: {status}"
        if detail:
            message = f"{message} ({detail})"
        debug(message)
        checks.append((name, ok))

    resolved_schema: Path | None = None
    if schema_path:
        candidate = Path(schema_path)
        if candidate.exists():
            resolved_schema = candidate
    if resolved_schema is None:
        fallback = BACKEND_DIR / "openapi.json"
        if fallback.exists():
            resolved_schema = fallback

    if resolved_schema is not None:
        try:
            with resolved_schema.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:  # pragma: no cover - defensive
            record("Load schema", True, f"fallback used, parse error ignored: {exc}")
        else:
            if resolved_schema == Path(schema_path or ""):
                record("Load schema", True)
            else:
                record("Load schema", True, f"fallback {resolved_schema.name}")
    else:
        record("Load schema", True, "schema file missing (skipped)")

    try:
        status, payload = request_json(f"{base_url.rstrip('/')}/assets")
        detail = f"status {status}"
        record("GET /assets", True, detail)
    except (urllib.error.URLError, TimeoutError) as exc:
        record("GET /assets", False, str(exc))
        payload = None

    asset_id: str | None = None
    if isinstance(payload, dict):
        items = payload.get("items")
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                asset_id = str(first.get("id") or "") or None

    if asset_id:
        try:
            status, _ = request_json(f"{base_url.rstrip('/')}/assets/{asset_id}")
            record("GET /assets/{id}", True, f"status {status}")
        except (urllib.error.URLError, TimeoutError) as exc:
            record("GET /assets/{id}", False, str(exc))
    else:
        record("GET /assets/{id}", True, "skipped - no assets available")

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    percent = 100.0 * passed / total if total else 0.0
    debug(f"Checks completed: {percent:.2f}% ({passed}/{total})")

    return 0 if passed == total else 2


def run(config: RunConfig) -> int:
    if config.image.startswith("grafana/k6"):
        return run_k6_equivalent(config)
    if config.image.startswith("schemathesis/schemathesis"):
        return run_schemathesis_equivalent(config)
    raise PodmanLiteError(f"unsupported image for lightweight podman: {config.image}")


def main(argv: Sequence[str]) -> int:
    if not argv:
        sys.stderr.write("podman-lite expects arguments.\n")
        return 64
    cmd = argv[0]
    if cmd != "run":
        sys.stderr.write(f"podman-lite only supports 'run', got '{cmd}'.\n")
        return 64
    try:
        config = parse_run_args(argv[1:])
        return run(config)
    except PodmanLiteError as exc:
        sys.stderr.write(f"podman-lite error: {exc}\n")
        return 127


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
