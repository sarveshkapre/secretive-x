from pathlib import Path

import pytest

from secretive_x.config import Config
from secretive_x.core import delete_key, read_public_key
from secretive_x.store import KeyRecord, ManifestError, load_manifest, save_manifest


def _record(private_key_path: Path, public_key_path: Path | str) -> KeyRecord:
    return KeyRecord(
        name="demo",
        provider="fido2",
        created_at="2020-01-01T00:00:00+00:00",
        public_key_path=str(public_key_path),
        private_key_path=str(private_key_path),
        comment="demo@secretive-x",
        resident=False,
        application=None,
    )


def test_read_public_key_blocks_path_outside_key_dir(tmp_path: Path) -> None:
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    manifest_path = tmp_path / "keys.json"
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=key_dir,
        manifest_path=manifest_path,
    )
    outside_pub = tmp_path / "outside.pub"
    outside_pub.write_text("ssh-ed25519 AAAA demo\n")
    record = _record(private_key_path=key_dir / "demo", public_key_path=outside_pub)

    with pytest.raises(ManifestError, match="outside key dir"):
        read_public_key(record, config=cfg)


def test_read_public_key_allows_relative_paths_under_key_dir(tmp_path: Path) -> None:
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    manifest_path = tmp_path / "keys.json"
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=key_dir,
        manifest_path=manifest_path,
    )
    pub_path = key_dir / "demo.pub"
    pub_path.write_text("ssh-ed25519 AAAA demo\n")
    record = _record(private_key_path=key_dir / "demo", public_key_path="demo.pub")
    assert read_public_key(record, config=cfg) == "ssh-ed25519 AAAA demo"


def test_delete_key_blocks_path_outside_key_dir_and_keeps_manifest(tmp_path: Path) -> None:
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    manifest_path = tmp_path / "keys.json"
    cfg = Config(
        config_path=tmp_path / "config.json",
        key_dir=key_dir,
        manifest_path=manifest_path,
    )
    record = _record(
        private_key_path=tmp_path / "outside",
        public_key_path=tmp_path / "outside.pub",
    )
    save_manifest(manifest_path, {"demo": record})

    with pytest.raises(ManifestError, match="outside key dir"):
        delete_key("demo", config=cfg)

    records = load_manifest(manifest_path)
    assert "demo" in records
