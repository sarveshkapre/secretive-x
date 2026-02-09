# Secretive-X

Secretive-X is a cross-platform CLI that creates **non-exportable SSH keys** using hardware-backed providers (FIDO2 security keys today) and manages them with a clean, auditable workflow. It wraps OpenSSH tooling, enforces safe defaults, and keeps a local manifest so you can rotate and track keys without leaking private material.

Status: **MVP (v0.1.0 target)** — FIDO2-backed keys are supported. Secure Enclave/TPM integrations are planned and documented in the roadmap.

## Features
- FIDO2-backed SSH keys via `ssh-keygen -t ed25519-sk`
- Local key inventory with metadata and integrity checks
- Provider filtering for key inventory (`list --provider`)
- Config policy guardrails for key creation (`allowed_providers`, `name_pattern`)
- Tamper-resistant manifest path handling for `pubkey`/`delete`
- Safe defaults (key naming validation, no overwrites, secure key directory)
- Provider-aware workflow and clear error reporting
- One-command diagnostics (`doctor`)

## Quickstart

Prereqs:
- OpenSSH with FIDO2 support (`ssh-keygen` supports `ed25519-sk`)
- A FIDO2 security key (e.g., YubiKey, SoloKey)

Install dev deps and run locally:

```bash
make setup
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Run a non-destructive smoke path:

```bash
make smoke
```

Create a FIDO2-backed key:

```bash
python3 -m secretive_x.cli init
python3 -m secretive_x.cli create --name work-laptop --provider fido2
```

List keys:

```bash
python3 -m secretive_x.cli list
```

List only software-backed keys:

```bash
python3 -m secretive_x.cli list --provider software
```

Show public key:

```bash
python3 -m secretive_x.cli pubkey work-laptop
```

## SSH config snippet

Generate a minimal SSH config entry:

```bash
python3 -m secretive_x.cli ssh-config --name work-laptop --host github.com
```

## Data locations
- Config: `~/.config/secretive-x/config.json`
- Keys: `~/.ssh/secretive-x/`
- Manifest: `~/.config/secretive-x/keys.json`

## Config policy guardrails
`config.json` supports optional policy fields enforced by `create`:

```json
{
  "allowed_providers": ["fido2", "software"],
  "name_pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"
}
```

## Limitations
- Secure Enclave and TPM providers are **not** implemented yet (see `docs/ROADMAP.md`).
- FIDO2 support depends on your local OpenSSH build.

## Docker
Not applicable. Secretive-X is a local CLI that relies on host OpenSSH and hardware tokens.

## Security notes
- Secretive-X never stores raw private key material for FIDO2 keys.
- For software keys, a passphrase is required unless explicitly disabled.

## License
MIT
