# PLAN

## Goal
Ship a production-ready CLI that creates and manages non-exportable SSH keys using hardware-backed providers (FIDO2 now; Secure Enclave/TPM later) with safe defaults and clear diagnostics.

## Stack
- Language: Python 3.11
- CLI: Typer
- Config/dirs: platformdirs
- Tests: pytest
- Lint: ruff
- Type check: mypy
- Security: bandit + pip-audit

Rationale: Python provides fast iteration and cross-platform support while keeping the binary footprint small. OpenSSH does the heavy crypto lifting.

## Architecture
- `cli.py`: CLI entrypoints and UX
- `core.py`: orchestration between config/store/ssh
- `store.py`: manifest handling (keys.json)
- `ssh.py`: OpenSSH command construction + execution
- `config.py`: config paths and defaults
- `utils.py`: validation and atomic file writes

Data:
- Config in `~/.config/secretive-x/config.json`
- Manifest in `~/.config/secretive-x/keys.json`
- Keys in `~/.ssh/secretive-x/`

## MVP scope
- Init command to create config and directories
- Create keys using FIDO2 provider (`ed25519-sk`)
- List keys + show pubkey
- Delete local key files + manifest cleanup
- Doctor command to validate prerequisites
- SSH config snippet generator

## Non-goals (MVP)
- Secure Enclave integration
- TPM integration
- GUI
- Remote sync

## Risks
- Host OpenSSH builds may lack FIDO2 support
- Hardware key PIN/touch UX varies across OS
- Windows OpenSSH path differences

## Milestones
1. Scaffold repo + docs + CI
2. Implement core CLI + tests
3. Security/lint/typecheck gate and smoke checks
4. v0.1.0 release

## MVP checklist
- [ ] `secretive-x init` works
- [ ] `secretive-x create --provider fido2` creates key
- [ ] `secretive-x list` shows key inventory
- [ ] `secretive-x pubkey <name>` outputs public key
- [ ] `secretive-x delete <name>` removes local key files
- [ ] `secretive-x doctor` reports `ssh-keygen` availability
- [ ] `make check` passes
