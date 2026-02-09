from __future__ import annotations

import getpass
import json
from enum import Enum
from pathlib import Path
from typing import NoReturn

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import ConfigError, default_config, init_config, load_config
from .core import (
    KeyExistsError,
    create_key,
    delete_key,
    get_key,
    list_keys,
    read_public_key,
    ssh_config_snippet,
)
from .ssh import SshError, check_ssh_keygen, get_ssh_version, ssh_supports_key_type
from .store import KeyRecord, ManifestError, load_manifest
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
    try:
        load_manifest(config.manifest_path)
    except ManifestError as exc:
        manifest_error = str(exc)

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
    if not has_keygen:
        raise typer.Exit(code=1)
    if config_error is not None or manifest_error is not None:
        raise typer.Exit(code=1)


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
    except ValueError as exc:
        _fail(str(exc), json_output=json_output, code=2)

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

    key = read_public_key(record)
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
