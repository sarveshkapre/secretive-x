from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import secretive_x.cli as cli
from secretive_x.config import Config, ConfigError
from secretive_x.store import KeyRecord, ManifestError

runner = CliRunner()


def _record(*, name: str = "demo", provider: str = "fido2", resident: bool = False) -> KeyRecord:
    return KeyRecord(
        name=name,
        provider=provider,
        created_at="2020-01-01T00:00:00+00:00",
        public_key_path=f"/tmp/{name}.pub",
        private_key_path=f"/tmp/{name}",
        comment=f"{name}@secretive-x",
        resident=resident,
        application=None,
    )


def test_delete_prompts_and_can_cancel(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())

    def _delete_key(name: str):
        raise AssertionError("delete_key should not be called when user cancels")

    monkeypatch.setattr(cli, "delete_key", _delete_key)
    result = runner.invoke(cli.app, ["delete", "demo"], input="n\n")
    assert result.exit_code == 0
    assert "Canceled" in result.stdout


def test_delete_yes_skips_prompt(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record(resident=True))
    calls: list[str] = []

    def _delete_key(name: str):
        calls.append(name)
        return _record(resident=True)

    monkeypatch.setattr(cli, "delete_key", _delete_key)
    result = runner.invoke(cli.app, ["delete", "demo", "--yes"])
    assert result.exit_code == 0
    assert calls == ["demo"]
    assert "Deleted demo" in result.stdout


def test_help_does_not_crash() -> None:
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "create" in result.stdout


def test_command_help_for_optional_params() -> None:
    for cmd in (["create", "--help"], ["pubkey", "--help"], ["ssh-config", "--help"]):
        result = runner.invoke(cli.app, cmd)
        assert result.exit_code == 0


def test_init_json_status_created(monkeypatch, tmp_path) -> None:
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=tmp_path / "keys",
        manifest_path=tmp_path / "keys.json",
    )
    monkeypatch.setattr(cli, "default_config", lambda: cfg)
    monkeypatch.setattr(cli, "init_config", lambda **kwargs: cfg)

    result = runner.invoke(cli.app, ["init", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "created"


def test_init_json_status_existing(monkeypatch, tmp_path) -> None:
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=tmp_path / "keys",
        manifest_path=tmp_path / "keys.json",
    )
    cfg.config_path.write_text("{}")
    monkeypatch.setattr(cli, "default_config", lambda: cfg)
    monkeypatch.setattr(cli, "init_config", lambda **kwargs: cfg)

    result = runner.invoke(cli.app, ["init", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "existing"


def test_init_json_status_overwritten(monkeypatch, tmp_path) -> None:
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=tmp_path / "keys",
        manifest_path=tmp_path / "keys.json",
    )
    cfg.config_path.write_text("{}")
    monkeypatch.setattr(cli, "default_config", lambda: cfg)
    monkeypatch.setattr(cli, "init_config", lambda **kwargs: cfg)

    result = runner.invoke(cli.app, ["init", "--json", "--force"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "overwritten"


def test_init_json_invalid_config(monkeypatch, tmp_path) -> None:
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=tmp_path / "keys",
        manifest_path=tmp_path / "keys.json",
    )
    monkeypatch.setattr(cli, "default_config", lambda: cfg)

    def _boom(**kwargs):
        raise ConfigError("bad config")

    monkeypatch.setattr(cli, "init_config", _boom)

    result = runner.invoke(cli.app, ["init", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert "Tip:" in payload["error"]


def test_list_json(monkeypatch) -> None:
    monkeypatch.setattr(cli, "list_keys", lambda: [_record(), _record(resident=True)])
    result = runner.invoke(cli.app, ["list", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["keys"][0]["name"] == "demo"
    assert "private_key_path" in payload["keys"][0]


def test_list_json_provider_filter(monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "list_keys",
        lambda: [
            _record(name="c", provider="fido2"),
            _record(name="a", provider="fido2"),
            _record(name="b", provider="software"),
        ],
    )
    result = runner.invoke(cli.app, ["list", "--json", "--provider", "fido2"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert [key["name"] for key in payload["keys"]] == ["a", "c"]
    assert all(key["provider"] == "fido2" for key in payload["keys"])


def test_create_json(monkeypatch) -> None:
    monkeypatch.setattr(cli, "validate_name", lambda n: n)
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(cli, "ssh_supports_key_type", lambda _: True)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
        ),
    )
    monkeypatch.setattr(cli, "create_key", lambda **kwargs: _record())
    result = runner.invoke(cli.app, ["create", "--name", "demo", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["created"]["name"] == "demo"


def test_create_fails_when_ssh_keygen_missing(monkeypatch) -> None:
    monkeypatch.setattr(cli, "validate_name", lambda n: n)
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: False)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
        ),
    )

    def _create_key(**kwargs):
        raise AssertionError("create_key should not be called when ssh-keygen is missing")

    monkeypatch.setattr(cli, "create_key", _create_key)
    result = runner.invoke(cli.app, ["create", "--name", "demo"])
    assert result.exit_code == 1
    assert "ssh-keygen was not found" in result.stdout


def test_create_fails_when_fido2_not_supported(monkeypatch) -> None:
    monkeypatch.setattr(cli, "validate_name", lambda n: n)
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(cli, "ssh_supports_key_type", lambda _: False)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
        ),
    )

    def _create_key(**kwargs):
        raise AssertionError("create_key should not be called when fido2 is unsupported")

    monkeypatch.setattr(cli, "create_key", _create_key)
    result = runner.invoke(cli.app, ["create", "--name", "demo", "--provider", "fido2"])
    assert result.exit_code == 1
    assert "does not advertise FIDO2 key support" in result.stdout


def test_create_rejects_resident_for_software(monkeypatch) -> None:
    monkeypatch.setattr(cli, "validate_name", lambda n: n)
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
        ),
    )

    def _create_key(**kwargs):
        raise AssertionError("create_key should not be called for invalid option combos")

    monkeypatch.setattr(cli, "create_key", _create_key)
    result = runner.invoke(
        cli.app,
        [
            "create",
            "--name",
            "demo",
            "--provider",
            "software",
            "--resident",
            "--no-passphrase",
        ],
    )
    assert result.exit_code == 2
    assert "only supported for --provider fido2" in result.stdout


def test_create_rejects_disallowed_provider_policy(monkeypatch) -> None:
    monkeypatch.setattr(cli, "validate_name", lambda n: n)
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
            allowed_providers=("fido2",),
        ),
    )

    def _create_key(**kwargs):
        raise AssertionError("create_key should not run for disallowed provider")

    monkeypatch.setattr(cli, "create_key", _create_key)
    result = runner.invoke(
        cli.app, ["create", "--name", "demo", "--provider", "software", "--no-passphrase"]
    )
    assert result.exit_code == 2
    assert "not allowed by config policy" in result.stdout


def test_create_rejects_name_pattern_policy(monkeypatch) -> None:
    monkeypatch.setattr(cli, "validate_name", lambda n: n)
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(cli, "ssh_supports_key_type", lambda _: True)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
            allowed_providers=("fido2", "software"),
            name_pattern=r"^corp-[a-z0-9-]+$",
        ),
    )

    def _create_key(**kwargs):
        raise AssertionError("create_key should not run for disallowed key name")

    monkeypatch.setattr(cli, "create_key", _create_key)
    result = runner.invoke(cli.app, ["create", "--name", "demo", "--provider", "fido2"])
    assert result.exit_code == 2
    assert "does not match configured name policy" in result.stdout


def test_pubkey_json(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(cli, "read_public_key", lambda record: "ssh-ed25519 AAAA demo")
    result = runner.invoke(cli.app, ["pubkey", "demo", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["name"] == "demo"
    assert payload["public_key"].startswith("ssh-")


def test_pubkey_json_manifest_error(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(
        cli,
        "read_public_key",
        lambda record: (_ for _ in ()).throw(ManifestError("unsafe public key path")),
    )
    result = runner.invoke(cli.app, ["pubkey", "demo", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["error"] == "unsafe public key path"


def test_pubkey_output_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(cli, "read_public_key", lambda record: "ssh-ed25519 AAAA demo")
    target = tmp_path / "demo.pub"
    result = runner.invoke(cli.app, ["pubkey", "demo", "--output", str(target)])
    assert result.exit_code == 0
    assert target.read_text().strip().startswith("ssh-ed25519")


def test_pubkey_output_file_requires_force(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(cli, "read_public_key", lambda record: "ssh-ed25519 AAAA demo")
    target = tmp_path / "demo.pub"
    target.write_text("existing")
    result = runner.invoke(cli.app, ["pubkey", "demo", "--output", str(target)])
    assert result.exit_code == 2
    assert "Output file exists" in result.stdout


def test_ssh_config_json(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(cli, "ssh_config_snippet", lambda record, host: f"Host {host}\n")
    result = runner.invoke(cli.app, ["ssh-config", "demo", "--host", "github.com", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["name"] == "demo"
    assert payload["host"] == "github.com"
    assert payload["snippet"].startswith("Host github.com")


def test_ssh_config_output_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(cli, "ssh_config_snippet", lambda record, host: f"Host {host}\n")
    target = tmp_path / "ssh_config"
    result = runner.invoke(
        cli.app, ["ssh-config", "demo", "--host", "github.com", "--output", str(target)]
    )
    assert result.exit_code == 0
    assert target.read_text().startswith("Host github.com")


def test_delete_json_requires_yes(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    result = runner.invoke(cli.app, ["delete", "demo", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert "Use --yes" in payload["error"]


def test_delete_json(monkeypatch) -> None:
    monkeypatch.setattr(cli, "get_key", lambda name: _record())
    monkeypatch.setattr(cli, "delete_key", lambda name: _record(resident=True))
    result = runner.invoke(cli.app, ["delete", "demo", "--json", "--yes"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["deleted"]["name"] == "demo"


def test_doctor_json(monkeypatch) -> None:
    monkeypatch.setattr(cli, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(cli, "get_ssh_version", lambda: "OpenSSH_9.9")
    monkeypatch.setattr(cli, "ssh_supports_key_type", lambda _: True)
    monkeypatch.setattr(
        cli,
        "default_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
        ),
    )
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: Config(
            config_path=Path("/tmp/config.json"),
            key_dir=Path("/tmp/keys"),
            manifest_path=Path("/tmp/keys.json"),
        ),
    )
    monkeypatch.setattr(cli, "load_manifest", lambda _: {})
    result = runner.invoke(cli.app, ["doctor", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ssh_keygen"] is True
    assert payload["ssh_version"] == "OpenSSH_9.9"
    assert payload["fido2_key_type_support"] is True


def test_info_json(monkeypatch, tmp_path) -> None:
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=tmp_path / "keys",
        manifest_path=tmp_path / "keys.json",
    )
    monkeypatch.setattr(cli, "load_config", lambda: cfg)
    result = runner.invoke(cli.app, ["info", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["config_path"].endswith("config.json")


def test_version_json() -> None:
    result = runner.invoke(cli.app, ["version", "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "version" in payload


def test_info_json_invalid_config(monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "load_config", lambda: (_ for _ in ()).throw(ConfigError("bad config"))
    )
    result = runner.invoke(cli.app, ["info", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert "error" in payload


def test_list_json_invalid_manifest(monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "list_keys", lambda: (_ for _ in ()).throw(ManifestError("bad manifest"))
    )
    result = runner.invoke(cli.app, ["list", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert "error" in payload
