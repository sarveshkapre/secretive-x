from __future__ import annotations

from pathlib import Path

from .config import Config, load_config
from .ssh import build_ssh_keygen_cmd, generate_key
from .store import KeyRecord, load_manifest, save_manifest


class KeyExistsError(RuntimeError):
    pass


def create_key(
    name: str,
    provider: str,
    comment: str,
    passphrase: str | None,
    resident: bool,
    application: str | None,
    rounds: int,
    config: Config | None = None,
) -> KeyRecord:
    config = config or load_config()
    config.key_dir.mkdir(parents=True, exist_ok=True)
    key_path = config.key_dir / name
    pub_path = config.key_dir / f"{name}.pub"

    if key_path.exists() or pub_path.exists():
        raise KeyExistsError(f"Key files already exist for {name}.")

    cmd = build_ssh_keygen_cmd(
        provider=provider,
        key_path=key_path,
        comment=comment,
        passphrase=passphrase,
        resident=resident,
        application=application,
        rounds=rounds,
    )
    generate_key(cmd)

    record = KeyRecord.new(
        name=name,
        provider=provider,
        public_key_path=pub_path,
        private_key_path=key_path,
        comment=comment,
        resident=resident,
        application=application,
    )
    records = load_manifest(config.manifest_path)
    records[name] = record
    save_manifest(config.manifest_path, records)
    return record


def delete_key(name: str, config: Config | None = None) -> KeyRecord | None:
    config = config or load_config()
    records = load_manifest(config.manifest_path)
    record = records.pop(name, None)
    if record is None:
        return None

    key_path = Path(record.private_key_path)
    pub_path = Path(record.public_key_path)
    if key_path.exists():
        key_path.unlink()
    if pub_path.exists():
        pub_path.unlink()

    save_manifest(config.manifest_path, records)
    return record


def list_keys(config: Config | None = None) -> list[KeyRecord]:
    config = config or load_config()
    records = load_manifest(config.manifest_path)
    return list(records.values())


def get_key(name: str, config: Config | None = None) -> KeyRecord | None:
    config = config or load_config()
    records = load_manifest(config.manifest_path)
    return records.get(name)


def read_public_key(record: KeyRecord) -> str:
    return Path(record.public_key_path).read_text().strip()


def ssh_config_snippet(record: KeyRecord, host: str) -> str:
    return (
        f"Host {host}\n"
        f"  IdentityFile {record.private_key_path}\n"
        "  IdentitiesOnly yes\n"
    )
