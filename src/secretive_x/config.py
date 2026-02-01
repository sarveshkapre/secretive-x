from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path

from .utils import atomic_write_json

APP_NAME = "secretive-x"


@dataclass(frozen=True)
class Config:
    config_path: Path
    key_dir: Path
    manifest_path: Path


def default_config() -> Config:
    config_dir = user_config_path(APP_NAME)
    config_path = config_dir / "config.json"
    key_dir = Path.home() / ".ssh" / "secretive-x"
    manifest_path = config_dir / "keys.json"
    return Config(config_path=config_path, key_dir=key_dir, manifest_path=manifest_path)


def load_config() -> Config:
    cfg = default_config()
    if not cfg.config_path.exists():
        return cfg
    data = json.loads(cfg.config_path.read_text())
    return Config(
        config_path=cfg.config_path,
        key_dir=Path(data.get("key_dir", cfg.key_dir)),
        manifest_path=Path(data.get("manifest_path", cfg.manifest_path)),
    )


def save_config(config: Config) -> None:
    atomic_write_json(
        config.config_path,
        {
            "version": 1,
            "key_dir": str(config.key_dir),
            "manifest_path": str(config.manifest_path),
        },
    )


def init_config() -> Config:
    config = default_config()
    config.key_dir.mkdir(parents=True, exist_ok=True)
    config.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    save_config(config)
    return config
