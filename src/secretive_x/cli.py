from __future__ import annotations

import getpass
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
from .ssh import SshError, check_ssh_keygen, get_ssh_version
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


@app.command()
def init() -> None:
    """Initialize config and directories."""
    config = init_config()
    console.print(f"Config: {config.config_path}")
    console.print(f"Keys:   {config.key_dir}")
    console.print(f"Store:  {config.manifest_path}")


@app.command()
def doctor() -> None:
    """Check local prerequisites."""
    has_keygen = check_ssh_keygen()
    version = get_ssh_version()
    console.print(f"ssh-keygen: {'OK' if has_keygen else 'MISSING'}")
    console.print(f"ssh version: {version or 'unknown'}")
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
def list_cmd() -> None:
    """List known keys."""
    records = list_keys()
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
def delete(name: str) -> None:
    """Delete local key files and remove from manifest."""
    record = delete_key(name)
    if record is None:
        console.print("Key not found.")
        raise typer.Exit(code=2)
    if record.provider == "fido2" and record.resident:
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
def info() -> None:
    """Show current config paths."""
    config = load_config()
    console.print(f"Config: {config.config_path}")
    console.print(f"Keys:   {config.key_dir}")
    console.print(f"Store:  {config.manifest_path}")


if __name__ == "__main__":
    app()
