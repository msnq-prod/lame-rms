from __future__ import annotations

from typing import Dict, Type

from pydantic import BaseModel

from . import assets as _assets
from . import generated as _generated

SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
    **_generated.SCHEMA_REGISTRY,
    **_assets.SCHEMA_REGISTRY,
}

__all__ = list(dict.fromkeys(list(_generated.__all__) + list(_assets.__all__)))

for name in _generated.__all__:
    globals()[name] = getattr(_generated, name)

for name in _assets.__all__:
    globals()[name] = getattr(_assets, name)
