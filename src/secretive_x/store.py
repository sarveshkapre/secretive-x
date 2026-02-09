from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .utils import atomic_write_json


class ManifestError(RuntimeError):
    pass


@dataclass
class KeyRecord:
    name: str
    provider: str
    created_at: str
    public_key_path: str
    private_key_path: str
    comment: str
    resident: bool
    application: str | None

    @staticmethod
    def new(
        name: str,
        provider: str,
        public_key_path: Path,
        private_key_path: Path,
        comment: str,
        resident: bool,
        application: str | None,
    ) -> KeyRecord:
        return KeyRecord(
            name=name,
            provider=provider,
            created_at=datetime.now(UTC).isoformat(),
            public_key_path=str(public_key_path),
            private_key_path=str(private_key_path),
            comment=comment,
            resident=resident,
            application=application,
        )


def load_manifest(path: Path) -> dict[str, KeyRecord]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in manifest file: {path}") from exc
    if not isinstance(data, dict):
        raise ManifestError(f"Invalid manifest schema: {path} (expected object root)")

    keys = data.get("keys", {})
    if not isinstance(keys, dict):
        raise ManifestError(f"Invalid manifest schema: {path} (keys must be an object)")

    try:
        records: dict[str, KeyRecord] = {}
        for name, payload in keys.items():
            if not isinstance(payload, dict):
                raise ManifestError(
                    f"Invalid manifest schema: {path} (entry '{name}' must be an object)"
                )
            records[name] = KeyRecord(**payload)
        return records
    except TypeError as exc:
        raise ManifestError(f"Invalid manifest schema: {path}") from exc


def save_manifest(path: Path, records: dict[str, KeyRecord]) -> None:
    atomic_write_json(
        path,
        {
            "version": 1,
            "keys": {name: asdict(record) for name, record in records.items()},
        },
    )
