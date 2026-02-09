from __future__ import annotations

from pathlib import Path

from .config import Config, load_config
from .ssh import build_ssh_keygen_cmd, generate_key
from .store import KeyRecord, ManifestError, load_manifest, save_manifest
from .utils import best_effort_chmod


class KeyExistsError(RuntimeError):
    pass


def _manifest_path_within_key_dir(path_value: str, *, key_dir: Path, field_name: str) -> Path:
    key_dir_resolved = key_dir.expanduser().resolve(strict=False)
    raw_path = Path(path_value).expanduser()
    candidate = raw_path if raw_path.is_absolute() else key_dir_resolved / raw_path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(key_dir_resolved)
    except ValueError as exc:
        raise ManifestError(
            "Invalid manifest entry: "
            f"{field_name} '{raw_path}' is outside key dir '{key_dir_resolved}'"
        ) from exc
    return resolved


def resolve_record_paths(record: KeyRecord, *, key_dir: Path) -> tuple[Path, Path]:
    """Resolve manifest paths against key_dir and enforce the key-dir trust boundary."""
    key_path = _manifest_path_within_key_dir(
        record.private_key_path, key_dir=key_dir, field_name="private_key_path"
    )
    pub_path = _manifest_path_within_key_dir(
        record.public_key_path, key_dir=key_dir, field_name="public_key_path"
    )
    return key_path, pub_path


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
    best_effort_chmod(config.key_dir, 0o700)
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
    record = records.get(name)
    if record is None:
        return None

    key_path, pub_path = resolve_record_paths(record, key_dir=config.key_dir)

    try:
        if key_path.exists():
            key_path.unlink()
        if pub_path.exists():
            pub_path.unlink()
    except OSError as exc:
        raise ManifestError(f"Failed to remove key files for {name}") from exc

    records.pop(name, None)
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


def read_public_key(record: KeyRecord, config: Config | None = None) -> str:
    config = config or load_config()
    _, pub_path = resolve_record_paths(record, key_dir=config.key_dir)
    try:
        return pub_path.read_text().strip()
    except OSError as exc:
        raise ManifestError(f"Failed to read public key file: {pub_path}") from exc


def ssh_config_snippet(record: KeyRecord, host: str) -> str:
    return (
        f"Host {host}\n"
        f"  IdentityFile {record.private_key_path}\n"
        "  IdentitiesOnly yes\n"
    )
