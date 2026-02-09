from __future__ import annotations

import getpass
import json
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import ConfigError, default_config, init_config, load_config, validate_creation_policy
from .core import (
    KeyExistsError,
    create_key,
    delete_key,
    get_key,
    list_keys,
    read_public_key,
    resolve_record_paths,
    ssh_config_snippet,
)
from .ssh import SshError, check_ssh_keygen, get_ssh_version, ssh_supports_key_type
from .store import KeyRecord, ManifestError, load_manifest, save_manifest
from .utils import atomic_write_text, validate_name

app = typer.Typer(no_args_is_help=True)
console = Console()


class Provider(str, Enum):
    fido2 = "fido2"
    software = "software"

NAME_OPTION = typer.Option(..., "--name", help="Key name, used as filename.")
PROVIDER_OPTION = typer.Option(Provider.fido2, "--provider")
COMMENT_OPTION = typer.Option(None, "--comment")
RESIDENT_OPTION = typer.Option(False, "--resident", help="Store key on device.")
APPLICATION_OPTION = typer.Option(None, "--application")
PASSPHRASE_OPTION = typer.Option(None, "--passphrase")
NO_PASSPHRASE_OPTION = typer.Option(False, "--no-passphrase")
ROUNDS_OPTION = typer.Option(64, "--rounds", help="KDF rounds for software keys.")
HOST_OPTION = typer.Option(..., "--host")
YES_OPTION = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt.")
JSON_OPTION = typer.Option(False, "--json", help="Output machine-readable JSON.")
OUTPUT_OPTION = typer.Option(None, "--output", help="Write output to file.")
FORCE_OUTPUT_OPTION = typer.Option(False, "--force", help="Overwrite output file.")
LIST_PROVIDER_OPTION = typer.Option(None, "--provider", help="Filter by provider.")
PRUNE_MISSING_OPTION = typer.Option(
    False,
    "--prune-missing",
    help="Remove manifest entries that reference missing key files (destructive).",
)
PRUNE_INVALID_PATHS_OPTION = typer.Option(
    False,
    "--prune-invalid-paths",
    help="Remove manifest entries with invalid/untrusted paths (destructive).",
)


def _print_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


def _record_to_json(record: KeyRecord) -> dict[str, object]:
    return {
        "application": record.application,
        "comment": record.comment,
        "created_at": record.created_at,
        "name": record.name,
        "private_key_path": record.private_key_path,
        "provider": record.provider,
        "public_key_path": record.public_key_path,
        "resident": record.resident,
    }


def _fail(message: str, *, json_output: bool = False, code: int = 1) -> NoReturn:
    if json_output:
        _print_json({"error": message})
    else:
        console.print(message)
    raise typer.Exit(code=code)


def _parse_pubkey_line(pubkey_line: str) -> tuple[str, str]:
    parts = pubkey_line.strip().split()
    if len(parts) < 2:
        raise ValueError("Invalid public key format (expected: <type> <base64> [comment])")
    key_type = parts[0]
    comment = parts[2] if len(parts) >= 3 else ""
    return key_type, comment


def _infer_provider_from_key_type(key_type: str) -> str:
    return "fido2" if key_type.startswith("sk-") else "software"


def _compute_manifest_drift(
    *,
    key_dir: Path,
    records: dict[str, KeyRecord],
) -> tuple[
    list[dict[str, str]],
    list[dict[str, object]],
    list[str],
    list[str],
    list[str],
]:
    invalid_manifest_paths: list[dict[str, str]] = []
    manifest_entries_missing_files: list[dict[str, object]] = []
    key_dir_untracked_pairs: list[str] = []
    key_dir_orphan_public_keys: list[str] = []
    key_dir_orphan_private_keys: list[str] = []

    for record in records.values():
        try:
            key_path, pub_path = resolve_record_paths(record, key_dir=key_dir)
        except ManifestError as exc:
            invalid_manifest_paths.append({"name": record.name, "error": str(exc)})
            continue

        missing: list[str] = []
        if not key_path.exists():
            missing.append("private")
        if not pub_path.exists():
            missing.append("public")
        if missing:
            manifest_entries_missing_files.append({"name": record.name, "missing": missing})

    try:
        tracked = set(records.keys())
        pub_names = set()
        for pub_path in key_dir.glob("*.pub"):
            name = pub_path.stem
            pub_names.add(name)
            priv_path = key_dir / name
            if not priv_path.exists():
                key_dir_orphan_public_keys.append(name)
                continue
            if name not in tracked:
                key_dir_untracked_pairs.append(name)

        for entry in key_dir.iterdir():
            if not entry.is_file():
                continue
            if entry.name.endswith(".pub"):
                continue
            # Name policy allows dots; use the `.pub` pairing convention instead of suffix checks.
            if (key_dir / f"{entry.name}.pub").exists():
                continue
            if entry.name in pub_names:
                continue
            key_dir_orphan_private_keys.append(entry.name)
    except OSError as exc:
        raise ManifestError("Failed to scan key directory for drift") from exc

    invalid_manifest_paths.sort(key=lambda item: item["name"])
    manifest_entries_missing_files.sort(key=lambda item: str(item["name"]))
    key_dir_untracked_pairs = sorted(set(key_dir_untracked_pairs))
    key_dir_orphan_public_keys = sorted(set(key_dir_orphan_public_keys))
    key_dir_orphan_private_keys = sorted(set(key_dir_orphan_private_keys))

    return (
        invalid_manifest_paths,
        manifest_entries_missing_files,
        key_dir_untracked_pairs,
        key_dir_orphan_public_keys,
        key_dir_orphan_private_keys,
    )


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing config."),
    json_output: bool = JSON_OPTION,
) -> None:
    """Initialize config and directories."""
    config_path = default_config().config_path
    existed = config_path.exists()
    try:
        config = init_config(force=force)
    except ConfigError as exc:
        _fail(
            f"{exc}\nTip: run `secretive-x init --force` to overwrite the config.",
            json_output=json_output,
            code=2,
        )

    if existed and force:
        status = "overwritten"
    elif existed:
        status = "existing"
    else:
        status = "created"
    if json_output:
        _print_json(
            {
                "status": status,
                "config_path": str(config.config_path),
                "key_dir": str(config.key_dir),
                "manifest_path": str(config.manifest_path),
            }
        )
        return

    console.print(f"Config status: {status}")
    console.print(f"Config: {config.config_path}")
    console.print(f"Keys:   {config.key_dir}")
    console.print(f"Store:  {config.manifest_path}")


@app.command()
def doctor(json_output: bool = JSON_OPTION) -> None:
    """Check local prerequisites."""
    has_keygen = check_ssh_keygen()
    version = get_ssh_version()
    fido2_support = ssh_supports_key_type("sk-ssh-ed25519@openssh.com")

    cfg_default = default_config()
    config_exists = cfg_default.config_path.exists()
    config_error: str | None = None
    try:
        config = load_config()
    except ConfigError as exc:
        config = cfg_default
        config_error = str(exc)

    key_dir_exists = config.key_dir.exists()
    key_dir_is_dir = config.key_dir.is_dir() if key_dir_exists else None

    manifest_exists = config.manifest_path.exists()
    manifest_error: str | None = None
    manifest_records: dict[str, KeyRecord] | None = None
    try:
        manifest_records = load_manifest(config.manifest_path)
    except ManifestError as exc:
        manifest_error = str(exc)

    drift_computed = manifest_error is None and bool(key_dir_exists and key_dir_is_dir)
    invalid_manifest_paths: list[dict[str, str]] = []
    manifest_entries_missing_files: list[dict[str, object]] = []
    key_dir_untracked_pairs: list[str] = []
    key_dir_orphan_public_keys: list[str] = []

    if drift_computed:
        records = manifest_records or {}
        for record in records.values():
            try:
                key_path, pub_path = resolve_record_paths(record, key_dir=config.key_dir)
            except ManifestError as exc:
                invalid_manifest_paths.append({"name": record.name, "error": str(exc)})
                continue

            missing: list[str] = []
            if not key_path.exists():
                missing.append("private")
            if not pub_path.exists():
                missing.append("public")
            if missing:
                manifest_entries_missing_files.append({"name": record.name, "missing": missing})

        try:
            for pub_path in config.key_dir.glob("*.pub"):
                name = pub_path.stem
                priv_path = config.key_dir / name
                if not priv_path.exists():
                    key_dir_orphan_public_keys.append(name)
                    continue
                if name not in records:
                    key_dir_untracked_pairs.append(name)
        except OSError:
            # Best-effort drift scan; prereq checks above already validate key_dir existence/type.
            drift_computed = False

        invalid_manifest_paths.sort(key=lambda item: item["name"])
        manifest_entries_missing_files.sort(key=lambda item: str(item["name"]))
        key_dir_untracked_pairs = sorted(set(key_dir_untracked_pairs))
        key_dir_orphan_public_keys = sorted(set(key_dir_orphan_public_keys))

    if json_output:
        _print_json(
            {
                "ssh_keygen": has_keygen,
                "ssh_version": version,
                "fido2_key_type_support": fido2_support,
                "config": {
                    "exists": config_exists,
                    "path": str(cfg_default.config_path),
                    "valid": config_error is None,
                    "error": config_error,
                },
                "key_dir": {
                    "path": str(config.key_dir),
                    "exists": key_dir_exists,
                    "is_dir": key_dir_is_dir,
                },
                "manifest": {
                    "exists": manifest_exists,
                    "path": str(config.manifest_path),
                    "valid": manifest_error is None,
                    "error": manifest_error,
                },
                "drift": {
                    "computed": drift_computed,
                    "invalid_manifest_paths": invalid_manifest_paths,
                    "manifest_entries_missing_files": manifest_entries_missing_files,
                    "key_dir_untracked_pairs": key_dir_untracked_pairs,
                    "key_dir_orphan_public_keys": key_dir_orphan_public_keys,
                },
            }
        )
    else:
        console.print(f"ssh-keygen: {'OK' if has_keygen else 'MISSING'}")
        console.print(f"ssh version: {version or 'unknown'}")
        if fido2_support is None:
            console.print("fido2 support: unknown")
        else:
            console.print(f"fido2 support: {'OK' if fido2_support else 'MISSING'}")
        if config_error is None:
            console.print(f"config: OK ({cfg_default.config_path})")
        else:
            console.print(f"config: INVALID ({cfg_default.config_path})")
            console.print(config_error)
        if key_dir_exists and key_dir_is_dir:
            console.print(f"key dir: OK ({config.key_dir})")
        else:
            console.print(f"key dir: MISSING ({config.key_dir})")
        if manifest_error is None:
            console.print(f"manifest: OK ({config.manifest_path})")
        else:
            console.print(f"manifest: INVALID ({config.manifest_path})")
            console.print(manifest_error)
        if drift_computed:
            if (
                not invalid_manifest_paths
                and not manifest_entries_missing_files
                and not key_dir_untracked_pairs
                and not key_dir_orphan_public_keys
            ):
                console.print("drift: OK")
            else:
                console.print(
                    "drift:"
                    f" invalid_paths={len(invalid_manifest_paths)}"
                    f" missing_files={len(manifest_entries_missing_files)}"
                    f" untracked_pairs={len(key_dir_untracked_pairs)}"
                    f" orphan_public={len(key_dir_orphan_public_keys)}"
                )
    if not has_keygen:
        raise typer.Exit(code=1)
    if config_error is not None or manifest_error is not None:
        raise typer.Exit(code=1)
    if invalid_manifest_paths:
        raise typer.Exit(code=1)


@app.command()
def scan(
    apply: bool = typer.Option(
        False,
        "--apply",
        help="Apply safe manifest repairs (import untracked pairs).",
    ),
    prune_missing: bool = PRUNE_MISSING_OPTION,
    prune_invalid_paths: bool = PRUNE_INVALID_PATHS_OPTION,
    yes: bool = YES_OPTION,
    json_output: bool = JSON_OPTION,
) -> None:
    """Scan for drift between the manifest and on-disk key directory and optionally repair it."""
    try:
        config = load_config()
        records = load_manifest(config.manifest_path)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)

    if not config.key_dir.exists() or not config.key_dir.is_dir():
        _fail(
            f"Key dir is missing or not a directory: {config.key_dir}",
            json_output=json_output,
            code=2,
        )

    (
        invalid_manifest_paths,
        manifest_entries_missing_files,
        key_dir_untracked_pairs,
        key_dir_orphan_public_keys,
        key_dir_orphan_private_keys,
    ) = _compute_manifest_drift(key_dir=config.key_dir, records=records)

    if json_output and not yes:
        if prune_missing and manifest_entries_missing_files:
            _fail(
                "Use --yes with --json for non-interactive prune operations.",
                json_output=True,
                code=2,
            )
        if prune_invalid_paths and invalid_manifest_paths:
            _fail(
                "Use --yes with --json for non-interactive prune operations.",
                json_output=True,
                code=2,
            )

    imported: list[dict[str, object]] = []
    skipped_imports: list[dict[str, str]] = []
    pruned_missing: list[dict[str, object]] = []
    pruned_invalid: list[dict[str, str]] = []

    if apply and key_dir_untracked_pairs:
        for name in key_dir_untracked_pairs:
            pub_path = config.key_dir / f"{name}.pub"
            priv_path = config.key_dir / name
            try:
                pub_line = pub_path.read_text().strip()
                key_type, comment = _parse_pubkey_line(pub_line)
                provider = _infer_provider_from_key_type(key_type)
                if not comment:
                    comment = f"{name}@secretive-x"
                created_at = datetime.fromtimestamp(pub_path.stat().st_mtime, tz=UTC).isoformat()
                record = KeyRecord(
                    name=name,
                    provider=provider,
                    created_at=created_at,
                    public_key_path=str(pub_path),
                    private_key_path=str(priv_path),
                    comment=comment,
                    resident=False,
                    application=None,
                )
                records[name] = record
                imported.append(_record_to_json(record))
            except (OSError, ValueError) as exc:
                skipped_imports.append({"name": name, "error": str(exc)})

    if prune_missing and manifest_entries_missing_files:
        if not yes and not json_output:
            confirmed = typer.confirm(
                f"Prune {len(manifest_entries_missing_files)} manifest entr"
                f"{'y' if len(manifest_entries_missing_files) == 1 else 'ies'} with missing files?",
                default=False,
            )
            if not confirmed:
                prune_missing = False

        if prune_missing:
            for missing_item in manifest_entries_missing_files:
                name = str(missing_item.get("name", ""))
                if name and name in records:
                    records.pop(name, None)
                    pruned_missing.append(missing_item)

    if prune_invalid_paths and invalid_manifest_paths:
        if not yes and not json_output:
            confirmed = typer.confirm(
                f"Prune {len(invalid_manifest_paths)} manifest entr"
                f"{'y' if len(invalid_manifest_paths) == 1 else 'ies'} with invalid paths?",
                default=False,
            )
            if not confirmed:
                prune_invalid_paths = False

        if prune_invalid_paths:
            for invalid_item in invalid_manifest_paths:
                name = str(invalid_item.get("name", ""))
                if name and name in records:
                    records.pop(name, None)
                    pruned_invalid.append(invalid_item)

    if imported or pruned_missing or pruned_invalid:
        try:
            save_manifest(config.manifest_path, records)
        except ManifestError as exc:
            _fail(str(exc), json_output=json_output, code=2)

        # Recompute drift after applying changes so exit code reflects remaining issues.
        (
            invalid_manifest_paths,
            manifest_entries_missing_files,
            key_dir_untracked_pairs,
            key_dir_orphan_public_keys,
            key_dir_orphan_private_keys,
        ) = _compute_manifest_drift(key_dir=config.key_dir, records=records)

    drift_present = bool(
        invalid_manifest_paths
        or manifest_entries_missing_files
        or key_dir_untracked_pairs
        or key_dir_orphan_public_keys
        or key_dir_orphan_private_keys
    )

    if json_output:
        _print_json(
            {
                "key_dir": str(config.key_dir),
                "manifest_path": str(config.manifest_path),
                "apply": {
                    "requested": apply,
                    "imported_count": len(imported),
                    "imported": imported,
                    "skipped": skipped_imports,
                    "prune_missing": {
                        "requested": prune_missing,
                        "pruned_count": len(pruned_missing),
                        "pruned": pruned_missing,
                    },
                    "prune_invalid_paths": {
                        "requested": prune_invalid_paths,
                        "pruned_count": len(pruned_invalid),
                        "pruned": pruned_invalid,
                    },
                },
                "drift": {
                    "invalid_manifest_paths": invalid_manifest_paths,
                    "manifest_entries_missing_files": manifest_entries_missing_files,
                    "key_dir_untracked_pairs": key_dir_untracked_pairs,
                    "key_dir_orphan_public_keys": key_dir_orphan_public_keys,
                    "key_dir_orphan_private_keys": key_dir_orphan_private_keys,
                },
            }
        )
    else:
        console.print(f"key dir: {config.key_dir}")
        console.print(f"manifest: {config.manifest_path}")
        if apply or prune_missing or prune_invalid_paths:
            console.print(
                "applied:"
                f" imported={len(imported)}"
                f" pruned_missing={len(pruned_missing)}"
                f" pruned_invalid_paths={len(pruned_invalid)}"
                f" skipped={len(skipped_imports)}"
            )
        if not drift_present:
            console.print("drift: OK")
        else:
            console.print(
                "drift:"
                f" invalid_paths={len(invalid_manifest_paths)}"
                f" missing_files={len(manifest_entries_missing_files)}"
                f" untracked_pairs={len(key_dir_untracked_pairs)}"
                f" orphan_public={len(key_dir_orphan_public_keys)}"
                f" orphan_private={len(key_dir_orphan_private_keys)}"
            )

    raise typer.Exit(code=1 if drift_present else 0)


@app.command()
def create(
    name: str = NAME_OPTION,
    provider: Provider = PROVIDER_OPTION,
    comment: str = COMMENT_OPTION,
    resident: bool = RESIDENT_OPTION,
    application: str = APPLICATION_OPTION,
    passphrase: str = PASSPHRASE_OPTION,
    no_passphrase: bool = NO_PASSPHRASE_OPTION,
    rounds: int = ROUNDS_OPTION,
    json_output: bool = JSON_OPTION,
) -> None:
    """Create a new key using the selected provider."""
    try:
        validate_name(name)
        config = load_config()
        validate_creation_policy(config, name=name, provider=provider.value)
    except (ValueError, ConfigError) as exc:
        _fail(str(exc), json_output=json_output, code=2)

    if provider == Provider.software and (resident or application is not None):
        _fail(
            "--resident/--application are only supported for --provider fido2.",
            json_output=json_output,
            code=2,
        )
    if provider == Provider.fido2 and (passphrase is not None or no_passphrase or rounds != 64):
        _fail(
            "--passphrase/--no-passphrase/--rounds are only supported for --provider software.",
            json_output=json_output,
            code=2,
        )

    if not check_ssh_keygen():
        _fail(
            "ssh-keygen was not found on PATH. Install OpenSSH (with FIDO2 support) and try again.",
            json_output=json_output,
            code=1,
        )
    if provider == Provider.fido2:
        fido2_support = ssh_supports_key_type("sk-ssh-ed25519@openssh.com")
        if fido2_support is False:
            _fail(
                "Your OpenSSH does not advertise FIDO2 key support for ed25519-sk. "
                "Upgrade OpenSSH and verify `ssh -Q key` includes 'sk-ssh-ed25519@openssh.com'.",
                json_output=json_output,
                code=1,
            )

    if provider == Provider.software:
        if passphrase and no_passphrase:
            _fail(
                "Use either --passphrase or --no-passphrase, not both.",
                json_output=json_output,
                code=2,
            )
        if passphrase is None and not no_passphrase:
            passphrase = getpass.getpass("Passphrase: ")
        if passphrase is None:
            # User explicitly opted out of a passphrase.
            passphrase = ""  # nosec

    if comment is None:
        comment = f"{name}@secretive-x"

    try:
        record = create_key(
            name=name,
            provider=provider.value,
            comment=comment,
            passphrase=passphrase if provider == Provider.software else None,
            resident=resident,
            application=application,
            rounds=rounds,
            config=config,
        )
    except KeyExistsError as exc:
        _fail(str(exc), json_output=json_output, code=2)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    except SshError as exc:
        _fail(str(exc), json_output=json_output, code=1)

    if json_output:
        _print_json({"created": _record_to_json(record)})
        return
    console.print(f"Created {record.name} ({record.provider})")


@app.command(name="list")
def list_cmd(
    provider: Provider = LIST_PROVIDER_OPTION,
    json_output: bool = JSON_OPTION,
) -> None:
    """List known keys."""
    try:
        records = list_keys()
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    records = sorted(records, key=lambda r: r.name)
    if provider is not None:
        records = [record for record in records if record.provider == provider.value]

    if json_output:
        _print_json({"keys": [_record_to_json(record) for record in records]})
        return

    if not records:
        console.print("No keys found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("Provider")
    table.add_column("Created")
    table.add_column("Resident")
    table.add_column("Key Path")

    for record in records:
        table.add_row(
            record.name,
            record.provider,
            record.created_at,
            "yes" if record.resident else "no",
            record.private_key_path,
        )

    console.print(table)


@app.command()
def pubkey(
    name: str,
    json_output: bool = JSON_OPTION,
    output: Path = OUTPUT_OPTION,
    force: bool = FORCE_OUTPUT_OPTION,
) -> None:
    """Print the public key for a named key."""
    try:
        record = get_key(name)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    if record is None:
        _fail("Key not found.", json_output=json_output, code=2)

    try:
        key = read_public_key(record)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    if output:
        if output.exists() and not force:
            _fail(f"Output file exists: {output}", json_output=json_output, code=2)
        atomic_write_text(output, key + "\n")
        if json_output:
            _print_json({"name": record.name, "output_path": str(output)})
        else:
            console.print(f"Wrote {output}")
        return
    if json_output:
        _print_json({"name": record.name, "public_key": key})
        return
    console.print(key)


@app.command()
def delete(name: str, yes: bool = YES_OPTION, json_output: bool = JSON_OPTION) -> None:
    """Delete local key files and remove from manifest."""
    if json_output and not yes:
        _fail(
            "Use --yes with --json for non-interactive delete.",
            json_output=True,
            code=2,
        )
    try:
        record = get_key(name)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    if record is None:
        _fail("Key not found.", json_output=json_output, code=2)

    if not yes:
        confirmed = typer.confirm(
            f"Delete key '{name}'? This removes local key files and the manifest entry.",
            default=False,
        )
        if not confirmed:
            if json_output:
                _print_json({"status": "canceled", "name": name})
            else:
                console.print("Canceled.")
            raise typer.Exit(code=0)

    try:
        deleted = delete_key(name)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    if deleted is None:
        # Manifest changed between confirmation and deletion.
        _fail("Key not found.", json_output=json_output, code=2)

    if json_output:
        _print_json({"deleted": _record_to_json(deleted)})
        return

    if deleted.provider == "fido2" and deleted.resident:
        console.print("Local handle removed. Resident key may remain on device.")
    console.print(f"Deleted {name}")


@app.command("ssh-config")
def ssh_config(
    name: str,
    host: str = HOST_OPTION,
    json_output: bool = JSON_OPTION,
    output: Path = OUTPUT_OPTION,
    force: bool = FORCE_OUTPUT_OPTION,
) -> None:
    """Emit an SSH config snippet for a key."""
    try:
        record = get_key(name)
    except (ConfigError, ManifestError) as exc:
        _fail(str(exc), json_output=json_output, code=2)
    if record is None:
        _fail("Key not found.", json_output=json_output, code=2)
    snippet = ssh_config_snippet(record, host)
    if output:
        if output.exists() and not force:
            _fail(f"Output file exists: {output}", json_output=json_output, code=2)
        atomic_write_text(output, snippet)
        if json_output:
            _print_json({"name": record.name, "host": host, "output_path": str(output)})
        else:
            console.print(f"Wrote {output}")
        return
    if json_output:
        _print_json({"name": record.name, "host": host, "snippet": snippet})
        return
    console.print(snippet)


@app.command()
def info(json_output: bool = JSON_OPTION) -> None:
    """Show current config paths."""
    try:
        config = load_config()
    except ConfigError as exc:
        _fail(str(exc), json_output=json_output, code=2)
    if json_output:
        _print_json(
            {
                "config_path": str(config.config_path),
                "key_dir": str(config.key_dir),
                "manifest_path": str(config.manifest_path),
            }
        )
        return
    console.print(f"Config: {config.config_path}")
    console.print(f"Keys:   {config.key_dir}")
    console.print(f"Store:  {config.manifest_path}")


@app.command()
def version(json_output: bool = JSON_OPTION) -> None:
    """Show the CLI version."""
    if json_output:
        _print_json({"version": __version__})
        return
    console.print(__version__)


if __name__ == "__main__":
    app()
