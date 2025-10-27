from __future__ import annotations
import importlib
from typing import Dict, Type

from app.db.base import Base

generated = importlib.import_module('.generated', __name__)
MODEL_REGISTRY: Dict[str, Type[Base]] = generated.MODEL_REGISTRY
__all__ = list(generated.__all__)
for name in __all__:
    globals()[name] = getattr(generated, name)

METADATA = Base.metadata
