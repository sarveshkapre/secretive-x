from __future__ import annotations

import json
from pathlib import Path

import pytest

from secretive_x.config import ConfigError, default_config, init_config, load_config


def test_load_config_invalid_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{not-json")

    with pytest.raises(ConfigError):
        load_config()


def test_init_config_does_not_overwrite_existing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    monkeypatch.setattr("secretive_x.config.Path.home", lambda: tmp_path)

    cfg_path = tmp_path / "config.json"
    custom_key_dir = tmp_path / "custom_keys"
    custom_manifest = tmp_path / "custom_manifest.json"
    cfg_path.write_text(
        json.dumps(
            {
                "version": 1,
                "key_dir": str(custom_key_dir),
                "manifest_path": str(custom_manifest),
            }
        )
    )
    before = cfg_path.read_text()

    cfg = init_config()
    assert cfg.key_dir == custom_key_dir
    assert cfg.manifest_path == custom_manifest
    assert cfg_path.read_text() == before
    assert cfg.key_dir.exists()
    assert cfg.manifest_path.parent.exists()


def test_init_config_force_overwrites_existing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    monkeypatch.setattr("secretive_x.config.Path.home", lambda: tmp_path)

    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "version": 1,
                "key_dir": str(tmp_path / "custom_keys"),
                "manifest_path": str(tmp_path / "custom_manifest.json"),
            }
        )
    )

    cfg_default = default_config()
    cfg = init_config(force=True)
    assert cfg == cfg_default

    after = json.loads(cfg_path.read_text())
    assert after["key_dir"] == str(cfg_default.key_dir)
    assert after["manifest_path"] == str(cfg_default.manifest_path)


def test_init_config_invalid_json_without_force_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    monkeypatch.setattr("secretive_x.config.Path.home", lambda: tmp_path)

    (tmp_path / "config.json").write_text("{not-json")
    with pytest.raises(ConfigError):
        init_config()


def test_init_config_invalid_json_with_force_recovers(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    monkeypatch.setattr("secretive_x.config.Path.home", lambda: tmp_path)

    (tmp_path / "config.json").write_text("{not-json")
    cfg = init_config(force=True)
    assert isinstance(cfg.config_path, Path)
    assert cfg.config_path.exists()


def test_load_config_invalid_root_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    (tmp_path / "config.json").write_text("[]")
    with pytest.raises(ConfigError, match="expected object root"):
        load_config()


def test_load_config_invalid_path_types(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"version": 1, "key_dir": 123, "manifest_path": []})
    )
    with pytest.raises(ConfigError, match="key_dir must be a string"):
        load_config()


def test_load_config_policy_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps(
            {
                "version": 1,
                "key_dir": str(tmp_path / "keys"),
                "manifest_path": str(tmp_path / "keys.json"),
                "allowed_providers": ["fido2"],
                "name_pattern": r"^corp-[a-z0-9-]+$",
            }
        )
    )
    cfg = load_config()
    assert cfg.allowed_providers == ("fido2",)
    assert cfg.name_pattern == r"^corp-[a-z0-9-]+$"


def test_load_config_invalid_allowed_providers_shape(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"allowed_providers": "fido2", "name_pattern": r"^[a-z]+$"})
    )
    with pytest.raises(ConfigError, match="allowed_providers must be a list"):
        load_config()


def test_load_config_unknown_allowed_provider(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({"allowed_providers": ["fido2", "secure-enclave"]})
    )
    with pytest.raises(ConfigError, match="unknown providers"):
        load_config()


def test_load_config_invalid_name_pattern_regex(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"name_pattern": "["}))
    with pytest.raises(ConfigError, match="invalid name_pattern regex"):
        load_config()
