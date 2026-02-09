# PLAN

## Product pitch
Secretive-X is a cross-platform CLI that creates and manages non-exportable SSH keys (FIDO2 today) with safe defaults, a local manifest, and clear diagnostics.

## Features (MVP)
- FIDO2-backed SSH keys via `ssh-keygen -t ed25519-sk`
- Local key inventory (manifest) with metadata
- Safe defaults (validation, no overwrites, secure key directory)
- Diagnostics (`doctor`) and SSH config snippet generation

## Top risks / unknowns
- Host OpenSSH builds may lack FIDO2 key support.
- Hardware key PIN/touch UX differs across OS.
- Windows OpenSSH + path handling differences.

## Commands
See `docs/PROJECT.md` for the full command list.

Quality gate:
```bash
make check
```

## Shipped (latest)
- Repo scaffold + CLI MVP (init/create/list/pubkey/delete/doctor/ssh-config).
- Safety + robustness: `delete` confirmation prompt with `--yes`, and `doctor` reports FIDO2 key type support when detectable.
- Compatibility: pin Click to a Typer-compatible version and add a CLI `--help` smoke test.
- Automation: `--json` output mode for `doctor`, `list`, and `info`.
- Reliability: graceful errors for malformed config/manifest, and `doctor` now checks config/manifest/key-dir health.
- UX/safety: `init` no longer overwrites an existing config unless `--force` is passed (also supports `--json`).
- Automation: `--json` output mode for `create`, `pubkey`, `ssh-config`, and `delete` (delete requires `--yes` when using `--json`).
- Automation: `version` command (supports `--json`).
- UX: `pubkey` and `ssh-config` can now write to files with `--output` and `--force`.
- Security/policy: config now supports creation guardrails (`allowed_providers`, `name_pattern`) enforced by `create`.
- Security hardening: `pubkey`/`delete` now reject manifest paths outside the configured key directory.
- Reliability: added core regression tests for path tampering and policy validation, plus CI matrix coverage on Python `3.11` and `3.13`.
- Reliability: added `make smoke` for an isolated non-destructive CLI runtime check.

## Next to ship
- Provider support: Secure Enclave (macOS) and TPM (Linux/Windows).
- Key lifecycle: resident key enumeration/removal flow for FIDO2 devices.
- Policy UX: per-environment policy presets/profiles for org rollouts.
