# CHANGELOG

## Unreleased
- Fix CLI compatibility for Python 3.11/Typer by avoiding unsupported optional union option annotations.
- Add `list --provider` filtering and deterministic key ordering for table/JSON output.
- Harden config parsing with explicit schema/type validation and actionable `ConfigError` messages.
- Harden manifest parsing with explicit root/`keys`/entry shape validation and actionable `ManifestError` messages.
- Add regression tests for malformed config/manifest schemas, list provider filtering, and command help paths.
- Stabilize CI secret scanning by running `gitleaks` with full git history (`fetch-depth: 0`) and removing unsupported action inputs.
- Add a confirmation prompt to `delete` (with `--yes/-y` to skip).
- Improve `doctor` output by reporting FIDO2 key type support and local config/manifest health when detectable.
- Add `--json` output mode to most commands for automation (`init`, `doctor`, `list`, `info`, `create`, `pubkey`, `ssh-config`, `delete`).
- Add actionable errors for malformed config/manifest files (instead of stack traces).
- Make `init` idempotent (no config overwrite by default) and add `--force` to overwrite config when needed.
- Add `version` command (with `--json`) for automation and scripts.
- Add `--output` + `--force` to `pubkey` and `ssh-config` for safe file writes.
- Pin Click to a Typer-compatible version and add a `--help` smoke test.

## 0.1.0
- Initial scaffolding and CLI MVP.
