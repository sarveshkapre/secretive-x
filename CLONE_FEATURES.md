# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration
- GitHub Actions failure runs (`ci` workflow)

## Candidate Features To Do
- [ ] P1 Add `scan --cleanup-orphans` with `--dry-run` and `--yes` to remove orphaned private/public files safely.
- [ ] P0 Implement Secure Enclave provider flow on macOS (create/list/delete parity with current providers).
- [ ] P0 Implement TPM provider flow for Linux/Windows (provider parity and preflight checks).
- [ ] P1 Add resident key enumeration and explicit removal commands for FIDO2 authenticators.
- [ ] P1 Add `doctor --strict` provider preflight mode (OpenSSH/FIDO2/TPM/Secure Enclave capability checks by provider).
- [ ] P1 Add policy profile presets for org rollouts on top of `allowed_providers` and `name_pattern`.
- [ ] P1 Add manifest schema `version` validation and migration scaffolding for forward compatibility.
- [ ] P1 Add backup/restore command for manifest snapshots with integrity checks.
- [ ] P1 Add optional `create --verify-required` for FIDO2 user-verification enforcement (`ssh-keygen -O verify-required`).
- [ ] P2 Add provider abstraction/module boundary to isolate future Secure Enclave/TPM implementations.
- [ ] P2 Add richer `doctor` remediation hints (next-step commands per failed check).
- [ ] P2 Add `list --sort` and `list --created-after` filters for operational inventory workflows.
- [ ] P2 Add explicit file-locking around manifest writes to reduce concurrent-write risk.
- [ ] P2 Add compact TUI status view for local operator workflows.
- [ ] P2 Add release automation (tag + changelog guard + artifact checksum generation).
- [ ] P2 Add fuzz-style malformed config/manifest parser tests for robustness hardening.
- [ ] P2 Add benchmark guardrails for large manifest/list/export operations.

### Scoring Lens (selected items)
- Orphan cleanup (`scan --cleanup-orphans`): impact high | effort medium | fit high | differentiation medium | risk medium | confidence medium
- Secure Enclave provider parity: impact high | effort high | fit high | differentiation high | risk medium-high | confidence medium

### Gap Map (2026-02-11, bounded market scan)
- Missing: Secure Enclave provider flow; TPM provider flow; resident-key enumeration/removal.
- Weak: automated cleanup for on-disk orphans; provider-specific strict preflight diagnostics.
- Parity: FIDO2 key creation, drift scanning/reconciliation, JSON automation output, config policy guardrails.
- Differentiator opportunities: policy profiles for org rollout, safer manifest lifecycle tools (backup/restore + migrations), stronger diagnostics/remediation UX.

## Implemented
- [x] 2026-02-11: Add `resident-import` command to wrap `ssh-keygen -K`, detect newly downloaded keypairs, and import them into the manifest with JSON/human output; also reuse shared keypair-import helpers for `scan --apply`.  
  Evidence: `src/secretive_x/cli.py`, `src/secretive_x/ssh.py`, `tests/test_cli.py`, `tests/test_ssh.py`, `README.md`, `docs/PROJECT.md`, `scripts/smoke_cli.py`.
- [x] 2026-02-10: Refactor CLI output file handling helpers to reduce duplication (centralized atomic file writes and repeated `--output`/`--json` guards) without changing behavior.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-10: Unify `doctor` drift computation with `scan` and report full drift (including orphan private keys) to prevent command divergence.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-10: Add `--output` + `--force` support for more JSON-producing commands (`info`, `version`, `create`, `delete`) for automation-friendly artifacts.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-10: Add audit export for key inventory snapshots: `export --format csv|json` with `--output` + `--force` and provider filtering.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`, `README.md`, `docs/PROJECT.md`.
- [x] 2026-02-09: Add destructive `scan` prune modes for drift cleanup: `--prune-missing` (removes manifest entries that reference missing key files) and `--prune-invalid-paths` (removes entries with invalid/untrusted paths).  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Add `--output` + `--force` support for JSON-producing commands (`doctor`, `list`, `scan`) to write machine-readable output to files without shell redirects.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`, `README.md`.
- [x] 2026-02-09: Add `scan` command to detect manifest/key-dir drift and optionally import untracked on-disk keypairs into the manifest (`--apply`), with `--json` output for automation.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`, `README.md`, `CHANGELOG.md`.
- [x] 2026-02-09: Harden atomic writes and directory creation with best-effort POSIX permissions (`0600` files, `0700` dirs) and ensure key dir uses secure permissions when created.  
  Evidence: `src/secretive_x/utils.py`, `src/secretive_x/config.py`, `src/secretive_x/core.py`, `tests/test_utils.py`.
- [x] 2026-02-09: Add a cross-platform CLI smoke script and expand CI with an OS matrix smoke job (ubuntu/macos/windows).  
  Evidence: `scripts/smoke_cli.py`, `.github/workflows/ci.yml`.
- [x] 2026-02-09: Make `make check` work after `make setup` by auto-using the `.venv` toolchain when present (no manual PATH tweaks).  
  Evidence: `Makefile`, `README.md`, `docs/PROJECT.md`.
- [x] 2026-02-09: Add `create` preflight checks so FIDO2 key creation fails fast with actionable errors when `ssh-keygen` is missing or OpenSSH lacks `ed25519-sk` support; reject provider-incompatible flags.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Extend `doctor` to report drift (manifest entries with missing key files; key files on disk not in manifest) in both human and `--json` output; treat invalid manifest paths as unhealthy.  
  Evidence: `src/secretive_x/cli.py`, `src/secretive_x/core.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Fixed Typer/Python 3.11 CI compatibility by removing optional union annotations from CLI option parameters and added command-help regression coverage.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Stabilized `gitleaks` CI by fetching full git history and removing unsupported `args` usage in the action.  
  Evidence: `.github/workflows/ci.yml`.
- [x] 2026-02-09: Added `list --provider` filtering and deterministic ordering for both JSON and table output.  
  Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Hardened config schema handling with explicit root/type validation and actionable errors.  
  Evidence: `src/secretive_x/config.py`, `tests/test_config.py`.
- [x] 2026-02-09: Hardened manifest schema handling with explicit root/keys/entry validation and actionable errors.  
  Evidence: `src/secretive_x/store.py`, `tests/test_store.py`.
- [x] 2026-02-09: Added config policy guardrails (`allowed_providers`, `name_pattern`) and enforced them in `create`.  
  Evidence: `src/secretive_x/config.py`, `src/secretive_x/cli.py`, `tests/test_config.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Hardened manifest path trust boundaries so `pubkey`/`delete` reject paths outside configured key dir.  
  Evidence: `src/secretive_x/core.py`, `tests/test_core.py`, `tests/test_cli.py`.
- [x] 2026-02-09: Expanded CI `check` coverage to Python `3.11` and `3.13`, verified green on run `21809972093`.  
  Evidence: `.github/workflows/ci.yml`.
- [x] 2026-02-09: Added non-destructive local smoke path (`make smoke`) for core CLI runtime checks.  
  Evidence: `Makefile`, `docs/PROJECT.md`.
- [x] 2026-02-09: Added structured project memory and incident tracking files for decision/incident continuity.  
  Evidence: `PROJECT_MEMORY.md`, `INCIDENTS.md`.
- [x] 2026-02-09: Synced product memory/docs for new behavior and verification evidence.  
  Evidence: `README.md`, `PLAN.md`, `CHANGELOG.md`, `UPDATE.md`, `docs/PROJECT.md`, `CLONE_FEATURES.md`.

## Insights
- Typer runtime compatibility can diverge across Python minors; local green runs on newer Python do not guarantee CI safety on Python 3.11.
- `gitleaks/gitleaks-action@v2` ignores unsupported `args` input and still scans git history by commit range, so shallow fetch can produce false-failure CI.
- Manifest/config schema validation needs explicit shape checks to avoid accidental stack traces from malformed user-edited JSON.
- Manifest paths are untrusted input; operations that read/delete key files must enforce key-dir boundaries.
- A dedicated `make smoke` path catches CLI/runtime regressions that unit tests with monkeypatching may miss.
- Market scan (untrusted external sources): mature SSH-key tools emphasize resident key workflows and hardware-backed storage (FIDO2, Secure Enclave/TPM), plus clear preflight diagnostics.
  - OpenSSH `ssh-keygen` and resident key docs: https://man.openbsd.org/ssh-keygen
  - OpenSSH release notes / FIDO2 key support context: https://www.openssh.com/releasenotes.html
  - Secretive (macOS) reference UX for Secure Enclave-backed SSH keys: https://github.com/maxgoedjen/secretive
  - Yubico FIDO2 SSH guidance (`-O resident`, `-O verify-required`, host-key ordering caveat): https://developers.yubico.com/SSH/Securing_SSH_with_FIDO2.html
  - Nitrokey FIDO2 SSH guidance (`ssh-keygen -K` resident retrieval and `id_ed25519_sk_rk_*` naming): https://docs.nitrokey.com/nitrokeys/features/fido2/ssh
  - 1Password SSH agent docs (consent-based agent UX, host/key matching guidance): https://developer.1password.com/docs/ssh/agent

## Notes
- This file is maintained by the autonomous clone loop.
