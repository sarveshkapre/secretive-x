# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration
- GitHub Actions failure runs (`ci` workflow)

## Candidate Features To Do
- [ ] P0 Add a non-destructive manifest reconciliation command (proposed: `secretive-x scan`) to detect and optionally fix drift between manifest and `key_dir` (import missing entries, report missing files); include `--json` and `--apply`.
- [ ] P1 Harden atomic writes with best-effort POSIX permissions (`0600` files, `0700` config dir) without breaking Windows.
- [ ] P0 Implement Secure Enclave provider flow on macOS (create/list/delete parity with current providers).
- [ ] P0 Implement TPM provider flow for Linux/Windows.
- [ ] P1 Add resident key enumeration/removal commands for FIDO2 hardware keys.
- [ ] P1 Add policy profiles/presets for org rollouts on top of `allowed_providers` + `name_pattern`.
- [ ] P1 Add SSH agent integration guidance/commands for key caching workflows.
- [ ] P2 Add audit export (`JSON`/`CSV`) for key inventory and lifecycle events.
- [ ] P2 Expand CI to an OS matrix (ubuntu/macos/windows) for basic CLI help + smoke-only coverage.
- [ ] P2 Add a provider plugin interface (or internal abstraction) to keep Secure Enclave/TPM additions isolated.

### Scoring Lens (selected items)
- `scan` reconciliation: impact high | effort medium | fit high | differentiation medium | risk medium | confidence medium
- POSIX permission hardening: impact medium | effort low | fit high | differentiation low | risk low | confidence medium

## Implemented
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

## Notes
- This file is maintained by the autonomous clone loop.
