from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel

SettingsConfigDict = dict[str, Any]


def _read_env_file(path: Path, encoding: str = "utf-8") -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw_line in path.read_text(encoding=encoding).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


class BaseSettings(BaseModel):
    """Minimal BaseSettings implementation compatible with Pydantic v2."""

    settings_config: SettingsConfigDict = {}

    def __init__(self, **data: Any) -> None:
        merged = {**self.__class__._load_env(), **data}
        super().__init__(**merged)

    @classmethod
    def _load_env(cls) -> dict[str, Any]:
        config = getattr(cls, "settings_config", {})
        env_prefix: str = config.get("env_prefix", "")
        case_sensitive: bool = config.get("case_sensitive", False)
        encoding: str = config.get("env_file_encoding", "utf-8")
        env_files_cfg = config.get("env_file")
        env_files: Iterable[str]
        if env_files_cfg is None:
            env_files = []
        elif isinstance(env_files_cfg, (str, Path)):
            env_files = [str(env_files_cfg)]
        else:
            env_files = [str(item) for item in env_files_cfg]

        file_env: dict[str, str] = {}
        for env_file in env_files:
            file_env.update(_read_env_file(Path(env_file), encoding=encoding))

        combined_env: dict[str, str] = {**file_env, **os.environ}
        values: dict[str, Any] = {}
        for field_name in cls.model_fields:
            if case_sensitive:
                candidates = [f"{env_prefix}{field_name}"]
            else:
                key = f"{env_prefix}{field_name}".upper()
                candidates = [key, key.lower(), key.replace("-", "_")]
            for candidate in candidates:
                if candidate in combined_env:
                    values[field_name] = combined_env[candidate]
                    break
        return values


__all__ = ["BaseSettings", "SettingsConfigDict"]
