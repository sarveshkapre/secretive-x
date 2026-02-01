from __future__ import annotations

from typer.testing import CliRunner

import secretive_x.cli as cli
from secretive_x.store import KeyRecord

runner = CliRunner()


def _record(*, resident: bool = False) -> KeyRecord:
    return KeyRecord(
        name="demo",
        provider="fido2",
        created_at="2020-01-01T00:00:00+00:00",
        public_key_path="/tmp/demo.pub",
        private_key_path="/tmp/demo",
        comment="demo@secretive-x",
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
