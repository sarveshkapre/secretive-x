from __future__ import annotations

import pytest

from secretive_x.config import ConfigError, load_config


def test_load_config_invalid_json(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("secretive_x.config.user_config_path", lambda _: tmp_path)
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text("{not-json")

    with pytest.raises(ConfigError):
        load_config()

