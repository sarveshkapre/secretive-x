from __future__ import annotations

import getpass
import json
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table

from .config import init_config, load_config
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
from .utils import validate_name

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


def _print_json(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command()
def init() -> None:
    """Initialize config and directories."""
    config = init_config()
    console.print(f"Config: {config.config_path}")
    console.print(f"Keys:   {config.key_dir}")
    console.print(f"Store:  {config.manifest_path}")


@app.command()
def doctor(json_output: bool = JSON_OPTION) -> None:
    """Check local prerequisites."""
    has_keygen = check_ssh_keygen()
    version = get_ssh_version()
    fido2_support = ssh_supports_key_type("sk-ssh-ed25519@openssh.com")
    if json_output:
        _print_json(
            {
                "ssh_keygen": has_keygen,
                "ssh_version": version,
                "fido2_key_type_support": fido2_support,
            }
        )
    else:
        console.print(f"ssh-keygen: {'OK' if has_keygen else 'MISSING'}")
        console.print(f"ssh version: {version or 'unknown'}")
        if fido2_support is None:
            console.print("fido2 support: unknown")
        else:
            console.print(f"fido2 support: {'OK' if fido2_support else 'MISSING'}")
    if not has_keygen:
        raise typer.Exit(code=1)


@app.command()
def create(
    name: str = NAME_OPTION,
    provider: Provider = PROVIDER_OPTION,
    comment: str | None = COMMENT_OPTION,
    resident: bool = RESIDENT_OPTION,
    application: str | None = APPLICATION_OPTION,
    passphrase: str | None = PASSPHRASE_OPTION,
    no_passphrase: bool = NO_PASSPHRASE_OPTION,
    rounds: int = ROUNDS_OPTION,
) -> None:
    """Create a new key using the selected provider."""
    try:
        validate_name(name)
    except ValueError as exc:
        console.print(str(exc))
        raise typer.Exit(code=2) from None

    if provider == Provider.software:
        if passphrase and no_passphrase:
            console.print("Use either --passphrase or --no-passphrase, not both.")
            raise typer.Exit(code=2)
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
        console.print(str(exc))
        raise typer.Exit(code=2) from None
    except SshError as exc:
        console.print(str(exc))
        raise typer.Exit(code=1) from None

    console.print(f"Created {record.name} ({record.provider})")


@app.command(name="list")
def list_cmd(json_output: bool = JSON_OPTION) -> None:
    """List known keys."""
    records = list_keys()
    if json_output:
        def _as_dict(record):
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

        _print_json({"keys": [_as_dict(r) for r in sorted(records, key=lambda r: r.name)]})
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
def pubkey(name: str) -> None:
    """Print the public key for a named key."""
    record = get_key(name)
    if record is None:
        console.print("Key not found.")
        raise typer.Exit(code=2)
    console.print(read_public_key(record))


@app.command()
def delete(name: str, yes: bool = YES_OPTION) -> None:
    """Delete local key files and remove from manifest."""
    record = get_key(name)
    if record is None:
        console.print("Key not found.")
        raise typer.Exit(code=2)

    if not yes:
        confirmed = typer.confirm(
            f"Delete key '{name}'? This removes local key files and the manifest entry.",
            default=False,
        )
        if not confirmed:
            console.print("Canceled.")
            raise typer.Exit(code=0)

    deleted = delete_key(name)
    if deleted is None:
        # Manifest changed between confirmation and deletion.
        console.print("Key not found.")
        raise typer.Exit(code=2)

    if deleted.provider == "fido2" and deleted.resident:
        console.print("Local handle removed. Resident key may remain on device.")
    console.print(f"Deleted {name}")


@app.command("ssh-config")
def ssh_config(name: str, host: str = HOST_OPTION) -> None:
    """Emit an SSH config snippet for a key."""
    record = get_key(name)
    if record is None:
        console.print("Key not found.")
        raise typer.Exit(code=2)
    console.print(ssh_config_snippet(record, host))


@app.command()
def info(json_output: bool = JSON_OPTION) -> None:
    """Show current config paths."""
    config = load_config()
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


if __name__ == "__main__":
    app()
