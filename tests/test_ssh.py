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


def test_ssh_supports_key_type_unknown(monkeypatch) -> None:
    from secretive_x import ssh

    monkeypatch.setattr(ssh.shutil, "which", lambda _: None)
    assert ssh.ssh_supports_key_type("sk-ssh-ed25519@openssh.com") is None


def test_ssh_supports_key_type_true_false(monkeypatch) -> None:
    import subprocess

    from secretive_x import ssh

    monkeypatch.setattr(ssh.shutil, "which", lambda _: "/usr/bin/ssh")
    monkeypatch.setattr(
        ssh.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="ssh-ed25519\nsk-ssh-ed25519@openssh.com\n",
            stderr="",
        ),
    )
    assert ssh.ssh_supports_key_type("sk-ssh-ed25519@openssh.com") is True
    assert ssh.ssh_supports_key_type("ssh-dss") is False
