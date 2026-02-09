from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path

from .utils import atomic_write_json

APP_NAME = "secretive-x"


class ConfigError(RuntimeError):
    pass


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
    try:
        data = json.loads(cfg.config_path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {cfg.config_path}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Invalid config schema: {cfg.config_path} (expected object root)")

    key_dir_raw = data.get("key_dir", str(cfg.key_dir))
    manifest_path_raw = data.get("manifest_path", str(cfg.manifest_path))
    if not isinstance(key_dir_raw, str):
        raise ConfigError(f"Invalid config schema: {cfg.config_path} (key_dir must be a string)")
    if not isinstance(manifest_path_raw, str):
        raise ConfigError(
            f"Invalid config schema: {cfg.config_path} (manifest_path must be a string)"
        )

    return Config(
        config_path=cfg.config_path,
        key_dir=Path(key_dir_raw),
        manifest_path=Path(manifest_path_raw),
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


def init_config(*, force: bool = False) -> Config:
    cfg_default = default_config()

    if cfg_default.config_path.exists() and not force:
        config = load_config()
    else:
        config = cfg_default
        save_config(config)

    config.key_dir.mkdir(parents=True, exist_ok=True)
    config.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    return config
