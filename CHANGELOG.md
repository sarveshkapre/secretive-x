# CHANGELOG

## Unreleased
- Add a confirmation prompt to `delete` (with `--yes/-y` to skip).
- Improve `doctor` output by reporting FIDO2 key type support and local config/manifest health when detectable.
- Add `--json` output mode to most commands for automation (`init`, `doctor`, `list`, `info`, `create`, `pubkey`, `ssh-config`, `delete`).
- Add actionable errors for malformed config/manifest files (instead of stack traces).
- Make `init` idempotent (no config overwrite by default) and add `--force` to overwrite config when needed.
- Add `version` command (with `--json`) for automation and scripts.
- Pin Click to a Typer-compatible version and add a `--help` smoke test.

## 0.1.0
- Initial scaffolding and CLI MVP.
