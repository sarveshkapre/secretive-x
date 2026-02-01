from pathlib import Path

from secretive_x.store import KeyRecord, load_manifest, save_manifest


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
