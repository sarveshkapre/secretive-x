# CHANGELOG

## Unreleased
- Add audit export for key inventory snapshots: `export --format csv|json` with `--output` + `--force`.
- Add `--output` + `--force` support for more JSON-producing commands (`info`, `version`, `create`, `delete`).
- Unify `doctor` drift computation with `scan` and report full drift (including orphan private keys).
- Add destructive `scan` prune modes to remove invalid manifest entries: `scan --prune-missing` (entries with missing key files) and `scan --prune-invalid-paths` (untrusted/out-of-dir paths).
- Add `--output` + `--force` support for JSON-producing commands (`doctor`, `list`, `scan`) to write machine-readable output to files without shell redirects.
- Add `scan` command to detect drift between manifest and key directory and optionally import untracked on-disk keypairs (`scan --apply`), with `--json` output for automation.
- Harden config/manifest atomic writes with best-effort POSIX permissions (`0600` files, `0700` dirs) and ensure key dir uses secure permissions when created.
- Expand CI with a cross-platform smoke job (ubuntu/macos/windows) for basic CLI runtime coverage.
- Make `make check` work after `make setup` by auto-using the `.venv` toolchain when present.
- Add `create` preflight checks so FIDO2 key creation fails fast with actionable errors when `ssh-keygen` is missing or OpenSSH lacks `ed25519-sk` support; reject provider-incompatible flags.
- Extend `doctor` to report manifest/key-dir drift (missing files, untracked pairs) in both human and `--json` output; treat invalid manifest paths as unhealthy.
- Add config policy guardrails for key creation (`allowed_providers`, `name_pattern`) and enforce them in `create`.
- Harden manifest path trust boundaries by rejecting `pubkey`/`delete` operations when paths fall outside configured key dir.
- Add regression tests for config policy parsing, policy enforcement, and tampered-manifest path handling.
- Add `make smoke` non-destructive CLI runtime path (`init`, `info`, `list`, `version` in isolated temp env).
- Expand CI `check` job to Python matrix (`3.11`, `3.13`).
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
