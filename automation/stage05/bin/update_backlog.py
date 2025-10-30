#!/usr/bin/env python3
"""Update migration backlog entries for stage 05 based on contract diff."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_DIFF_PATH = REPO_ROOT / "automation" / "stage05" / "contract_diff.json"
BACKLOG_PATH = REPO_ROOT / "docs" / "backlog" / "migration_backlog.yaml"

GROUP_CONFIG: dict[str, dict[str, Any]] = {
    "barcodes": {
        "id": "M5-002",
        "title": "Assets barcode workflows parity",
        "description": (
            "Implement FastAPI endpoints covering barcode assignment, removal, and discovery "
            "so that inventory scans remain functional during the migration."
        ),
        "estimate": 8,
        "dependencies": ["M5-001"],
        "components": ["api", "assets", "barcodes"],
    },
    "crud": {
        "id": "M5-003",
        "title": "Assets CRUD and asset-type management parity",
        "description": (
            "Provide create, update, delete, listing, and search operations for assets and asset types "
            "in FastAPI to unlock end-to-end inventory management."
        ),
        "estimate": 13,
        "dependencies": ["M5-001"],
        "components": ["api", "assets"],
    },
    "export": {
        "id": "M5-004",
        "title": "Assets export parity",
        "description": (
            "Reproduce the legacy CSV export pipeline for assets with FastAPI endpoints and background tasks."
        ),
        "estimate": 5,
        "dependencies": ["M5-003"],
        "components": ["api", "assets", "reports"],
    },
}


def load_contract_diff(path: Path) -> list[dict[str, Any]]:
    """Return the list of endpoints missing in the new implementation."""

    if not path.exists():
        raise FileNotFoundError(f"Contract diff not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = data.get("missing_in_new", [])
    return [item for item in missing if isinstance(item, dict)]


def classify_endpoint(endpoint: dict[str, Any]) -> str:
    """Classify endpoint into barcode/CRUD/export groups."""

    path = str(endpoint.get("path", "")).lower()
    summary = str(endpoint.get("summary", "")).lower()
    if "barcode" in path or "barcode" in summary:
        return "barcodes"
    if "export" in path or "export" in summary:
        return "export"
    return "crud"


def group_endpoints(endpoints: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in GROUP_CONFIG}
    for endpoint in endpoints:
        group = classify_endpoint(endpoint)
        grouped.setdefault(group, []).append(endpoint)
    # Remove empty groups that are not configured
    return {key: value for key, value in grouped.items() if key in GROUP_CONFIG and value}


def ensure_backlog_structure(raw: Any) -> dict[str, Any]:
    data: dict[str, Any]
    if isinstance(raw, dict):
        data = raw
    else:
        data = {}
    data.setdefault("version", 1)
    data.setdefault("items", [])
    return data


def merge_entry(existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def build_entry(group: str, endpoints: list[dict[str, Any]]) -> dict[str, Any]:
    config = GROUP_CONFIG[group]
    legacy_routes = [f"{ep.get('method', '').upper()} {ep.get('path', '')}" for ep in endpoints]
    description = config["description"]
    description_suffix = (
        f" Legacy parity required for {len(legacy_routes)} route(s): "
        + ", ".join(legacy_routes)
    )
    entry = {
        "id": config["id"],
        "stage": 5,
        "domain": "assets",
        "title": config["title"],
        "description": description + description_suffix,
        "estimate": config["estimate"],
        "dependencies": config["dependencies"],
        "components": config["components"],
        "legacy_routes": legacy_routes,
    }
    return entry


def update_backlog(backlog_path: Path, groups: dict[str, list[dict[str, Any]]]) -> bool:
    raw = yaml.safe_load(backlog_path.read_text(encoding="utf-8")) if backlog_path.exists() else {}
    data = ensure_backlog_structure(raw)
    items: List[dict[str, Any]] = list(data.get("items", []))
    index: Dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict) and item.get("id"):
            index[item["id"]] = item

    changed = False
    for group, endpoints in groups.items():
        entry = build_entry(group, endpoints)
        entry_id = entry["id"]
        if entry_id in index:
            existing = index[entry_id]
            updated = merge_entry(existing, entry)
            if updated != existing:
                item_idx = items.index(existing)
                items[item_idx] = updated
                index[entry_id] = updated
                changed = True
        else:
            items.append(entry)
            index[entry_id] = entry
            changed = True

    if not changed:
        return False

    data["items"] = items
    data["total_items"] = len(items)
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    backlog_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return True


def main() -> None:
    endpoints = load_contract_diff(CONTRACT_DIFF_PATH)
    groups = group_endpoints(endpoints)
    if not groups:
        print("No endpoints require backlog updates.")
        return
    updated = update_backlog(BACKLOG_PATH, groups)
    if updated:
        print("Backlog updated.")
    else:
        print("Backlog already up to date.")


if __name__ == "__main__":
    main()
