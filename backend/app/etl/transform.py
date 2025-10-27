from __future__ import annotations

from typing import Any, Dict, List

from app.schemas import SCHEMA_REGISTRY


def transform_raw(raw: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Validate and coerce raw rows using the generated Pydantic schemas."""
    transformed: Dict[str, List[Dict[str, Any]]] = {}
    for table, rows in raw.items():
        schema = SCHEMA_REGISTRY.get(table)
        if schema is None:
            continue
        transformed_rows: List[Dict[str, Any]] = []
        for row in rows:
            model = schema.model_validate(row)
            transformed_rows.append(model.model_dump(mode="python", exclude_none=True))
        transformed[table] = transformed_rows
    return transformed
