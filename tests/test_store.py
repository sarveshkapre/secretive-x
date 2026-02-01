import json
from pathlib import Path

import pytest

from secretive_x.store import KeyRecord, ManifestError, load_manifest, save_manifest


def test_manifest_roundtrip(tmp_path: Path) -> None:
    manifest = tmp_path / "keys.json"
    record = KeyRecord.new(
        name="demo",
        provider="fido2",
        public_key_path=tmp_path / "demo.pub",
        private_key_path=tmp_path / "demo",
        comment="demo@secretive-x",
        resident=False,
        application=None,
    )
    save_manifest(manifest, {"demo": record})

    loaded = load_manifest(manifest)
    assert "demo" in loaded
    assert loaded["demo"].provider == "fido2"


def test_manifest_invalid_json(tmp_path: Path) -> None:
    manifest = tmp_path / "keys.json"
    manifest.write_text("{not-json")
    with pytest.raises(ManifestError):
        load_manifest(manifest)


def test_manifest_invalid_schema(tmp_path: Path) -> None:
    manifest = tmp_path / "keys.json"
    manifest.write_text(json.dumps({"version": 1, "keys": {"demo": {"name": "demo"}}}))
    with pytest.raises(ManifestError):
        load_manifest(manifest)
