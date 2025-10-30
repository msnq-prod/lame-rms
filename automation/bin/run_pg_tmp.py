#!/usr/bin/env python3
"""Start a temporary PostgreSQL instance and print its SQLAlchemy URI."""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import quote_plus

from testing.postgresql import Postgresql


@dataclass
class TempDatabase:
    """Lightweight wrapper around ``testing.postgresql.Postgresql``."""

    instance: Postgresql

    @property
    def uri(self) -> str:
        dsn = self.instance.dsn()
        user = quote_plus(dsn.get("user", ""))
        password = dsn.get("password") or ""
        host = dsn.get("host", "localhost")
        port = dsn.get("port")
        database = quote_plus(dsn.get("database", "postgres"))
        if password:
            password = f":{quote_plus(password)}"
        return f"postgresql+psycopg://{user}{password}@{host}:{port}/{database}"

    def describe(self) -> Dict[str, Any]:
        info = self.instance.dsn().copy()
        info["uri"] = self.uri
        proc = getattr(self.instance, "_proc", None)
        if proc is not None:
            info["pid"] = getattr(proc, "pid", None)
        return info

    def stop(self) -> None:
        self.instance.stop()


def start_temp_db() -> TempDatabase:
    return TempDatabase(Postgresql())


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Start a temporary PostgreSQL instance using testing.postgresql and "
            "print its connection URI. The process blocks until it receives "
            "SIGINT or SIGTERM, at which point the instance is stopped."
        )
    )
    parser.add_argument(
        "--format",
        choices=["uri", "json"],
        default="uri",
        help="Output format for connection details (default: uri)",
    )
    args = parser.parse_args()

    temp_db = start_temp_db()

    def _cleanup(*_: Any) -> None:
        try:
            temp_db.stop()
        finally:
            sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    payload: str
    if args.format == "json":
        payload = json.dumps(temp_db.describe())
    else:
        payload = temp_db.uri

    sys.stdout.write(payload + "\n")
    sys.stdout.flush()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _cleanup()


if __name__ == "__main__":
    main()
