from pathlib import Path

import pytest

from secretive_x.ssh import SshError, build_ssh_keygen_cmd, download_resident_keys


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


def test_download_resident_keys_uses_key_dir(monkeypatch, tmp_path) -> None:
    import subprocess

    from secretive_x import ssh

    monkeypatch.setattr(ssh, "check_ssh_keygen", lambda: True)
    seen: dict[str, object] = {}

    def _run(cmd, **kwargs):
        seen["cmd"] = cmd
        seen["cwd"] = kwargs.get("cwd")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(ssh.subprocess, "run", _run)
    stdout, stderr = download_resident_keys(tmp_path)
    assert stdout == "ok"
    assert stderr == ""
    assert seen["cmd"] == ["ssh-keygen", "-K"]
    assert seen["cwd"] == tmp_path


def test_download_resident_keys_requires_ssh_keygen(monkeypatch, tmp_path) -> None:
    from secretive_x import ssh

    monkeypatch.setattr(ssh, "check_ssh_keygen", lambda: False)
    with pytest.raises(SshError, match="not found"):
        download_resident_keys(tmp_path)


def test_download_resident_keys_surfaces_failure(monkeypatch, tmp_path) -> None:
    import subprocess

    from secretive_x import ssh

    monkeypatch.setattr(ssh, "check_ssh_keygen", lambda: True)
    monkeypatch.setattr(
        ssh.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0], returncode=1, stdout="", stderr="No FIDO authenticator"
        ),
    )
    with pytest.raises(SshError, match="No FIDO authenticator"):
        download_resident_keys(tmp_path)
