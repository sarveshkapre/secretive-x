from pathlib import Path

from secretive_x.ssh import build_ssh_keygen_cmd


def test_build_fido2_cmd() -> None:
    cmd = build_ssh_keygen_cmd(
        provider="fido2",
        key_path=Path("/tmp/demo"),
        comment="demo",
        passphrase=None,
        resident=True,
        application="ssh:demo",
        rounds=64,
    )
    assert "ed25519-sk" in cmd
    assert "resident" in " ".join(cmd)


def test_build_software_cmd() -> None:
    cmd = build_ssh_keygen_cmd(
        provider="software",
        key_path=Path("/tmp/demo"),
        comment="demo",
        passphrase="secret",
        resident=False,
        application=None,
        rounds=32,
    )
    assert "ed25519" in cmd
    assert "-N" in cmd
