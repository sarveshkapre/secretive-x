from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path

from .utils import atomic_write_json

APP_NAME = "secretive-x"
SUPPORTED_PROVIDERS = frozenset({"fido2", "software"})
DEFAULT_ALLOWED_PROVIDERS = ("fido2", "software")
DEFAULT_NAME_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    config_path: Path
    key_dir: Path
    manifest_path: Path
    allowed_providers: tuple[str, ...] = DEFAULT_ALLOWED_PROVIDERS
    name_pattern: str = DEFAULT_NAME_PATTERN


def default_config() -> Config:
    config_dir = user_config_path(APP_NAME)
    config_path = config_dir / "config.json"
    key_dir = Path.home() / ".ssh" / "secretive-x"
    manifest_path = config_dir / "keys.json"
    return Config(
        config_path=config_path,
        key_dir=key_dir,
        manifest_path=manifest_path,
        allowed_providers=DEFAULT_ALLOWED_PROVIDERS,
        name_pattern=DEFAULT_NAME_PATTERN,
    )


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
    allowed_providers_raw = data.get("allowed_providers", list(DEFAULT_ALLOWED_PROVIDERS))
    name_pattern_raw = data.get("name_pattern", DEFAULT_NAME_PATTERN)
    if not isinstance(key_dir_raw, str):
        raise ConfigError(f"Invalid config schema: {cfg.config_path} (key_dir must be a string)")
    if not isinstance(manifest_path_raw, str):
        raise ConfigError(
            f"Invalid config schema: {cfg.config_path} (manifest_path must be a string)"
        )
    if not isinstance(name_pattern_raw, str):
        raise ConfigError(
            f"Invalid config schema: {cfg.config_path} (name_pattern must be a string)"
        )
    if not isinstance(allowed_providers_raw, list):
        raise ConfigError(
            f"Invalid config schema: {cfg.config_path} (allowed_providers must be a list)"
        )
    if not allowed_providers_raw:
        raise ConfigError(
            f"Invalid config schema: {cfg.config_path} (allowed_providers cannot be empty)"
        )
    if any(not isinstance(provider, str) or not provider for provider in allowed_providers_raw):
        raise ConfigError(
            "Invalid config schema: "
            f"{cfg.config_path} (allowed_providers must contain non-empty strings)"
        )

    unknown_providers = sorted(set(allowed_providers_raw) - SUPPORTED_PROVIDERS)
    if unknown_providers:
        raise ConfigError(
            "Invalid config schema: "
            f"{cfg.config_path} (unknown providers: {', '.join(unknown_providers)})"
        )

    try:
        re.compile(name_pattern_raw)
    except re.error as exc:
        raise ConfigError(
            f"Invalid config schema: {cfg.config_path} (invalid name_pattern regex)"
        ) from exc

    allowed_providers = tuple(dict.fromkeys(allowed_providers_raw))

    return Config(
        config_path=cfg.config_path,
        key_dir=Path(key_dir_raw),
        manifest_path=Path(manifest_path_raw),
        allowed_providers=allowed_providers,
        name_pattern=name_pattern_raw,
    )


def save_config(config: Config) -> None:
    atomic_write_json(
        config.config_path,
        {
            "version": 1,
            "key_dir": str(config.key_dir),
            "manifest_path": str(config.manifest_path),
            "allowed_providers": list(config.allowed_providers),
            "name_pattern": config.name_pattern,
        },
    )


def validate_creation_policy(config: Config, *, name: str, provider: str) -> None:
    if provider not in config.allowed_providers:
        raise ConfigError(
            f"Provider '{provider}' is not allowed by config policy. "
            f"Allowed providers: {', '.join(config.allowed_providers)}."
        )

    try:
        pattern = re.compile(config.name_pattern)
    except re.error as exc:
        raise ConfigError(
            f"Invalid config schema: {config.config_path} (invalid name_pattern regex)"
        ) from exc

    if pattern.fullmatch(name) is None:
        raise ConfigError(
            f"Key name '{name}' does not match configured name policy: {config.name_pattern}"
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
