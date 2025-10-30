from __future__ import annotations

from typing import Dict, Type

from pydantic import BaseModel

from . import assets as _assets
from . import generated as _generated
from . import integrations as _integrations

_COMBINED_SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = {
    **_generated.SCHEMA_REGISTRY,
    **_assets.SCHEMA_REGISTRY,
    **getattr(_integrations, "SCHEMA_REGISTRY", {}),
}

SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = dict(_COMBINED_SCHEMA_REGISTRY)

__all__ = list(
    dict.fromkeys(list(_generated.__all__) + list(_assets.__all__) + list(_integrations.__all__))
)

for name in _generated.__all__:
    globals()[name] = getattr(_generated, name)

for name in _assets.__all__:
    globals()[name] = getattr(_assets, name)

for name in _integrations.__all__:
    globals()[name] = getattr(_integrations, name)

globals()["SCHEMA_REGISTRY"] = dict(_COMBINED_SCHEMA_REGISTRY)
