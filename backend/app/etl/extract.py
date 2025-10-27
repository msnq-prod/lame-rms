from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def extract_from_json(source: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Extract data from a JSON dump produced from MySQL."""
    with source.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Expected top-level object with table arrays")
    result: Dict[str, List[Dict[str, Any]]] = {}
    for table, rows in payload.items():
        if not isinstance(rows, list):
            raise ValueError(f"Table {table} must contain a list of rows")
        normalised: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"Row for {table} must be an object")
            normalised.append(row)
        result[table] = normalised
    return result
