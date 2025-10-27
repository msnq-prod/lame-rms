from __future__ import annotations
import importlib
from typing import Dict, Type

from pydantic import BaseModel

generated = importlib.import_module('.generated', __name__)
SCHEMA_REGISTRY: Dict[str, Type[BaseModel]] = generated.SCHEMA_REGISTRY
__all__ = list(generated.__all__)
for name in __all__:
    globals()[name] = getattr(generated, name)
