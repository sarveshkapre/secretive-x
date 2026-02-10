# PROJECT_MEMORY

## Decisions

### 2026-02-10: Unify `doctor` drift computation with `scan`
- Decision: `doctor` now reuses the shared drift scanner (`_compute_manifest_drift`) and reports orphan private keys for full parity with `scan`.
- Why: Keeping drift logic duplicated across commands invites divergence and inconsistent user diagnoses; parity improves reliability and makes drift output more trustworthy.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- Commit: `e81b0de`.
- Confidence: high.
- Trust label: verified-local-tests.

### 2026-02-10: Add `--output` for additional JSON-producing commands
- Decision: Added `--output` + `--force` to `info`, `version`, `create`, and `delete` in `--json` mode to produce file artifacts without shell redirects.
- Why: Automation and scripts benefit from stable, explicit JSON artifacts; extending parity reduces “special-case” handling across commands.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- Commit: `03926d5`.
- Confidence: high.
- Trust label: verified-local-tests.

### 2026-02-10: Add audit export command (`export --format csv|json`)
- Decision: Added `export` to dump key inventory snapshots as CSV or JSON, with provider filtering and safe file output (`--output` + `--force`).
- Why: Auditing and inventory workflows often need a portable snapshot format (CSV for spreadsheets, JSON for pipelines) without depending on table output parsing.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`, `README.md`, `docs/PROJECT.md`.
- Commit: `4b9aa5c`.
- Confidence: high.
- Trust label: verified-local-tests.

### 2026-02-09: Add `scan` prune modes for drift cleanup
- Decision: Added destructive `scan` prune flags to remove invalid manifest entries: `--prune-missing` (entries referencing missing key files) and `--prune-invalid-paths` (entries with invalid/untrusted paths).
- Why: Drift is common and can leave the manifest with entries that will never work (missing files) or are actively unsafe (paths outside the configured key dir); pruning provides an explicit, auditable cleanup path.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- Commit: `3d28c7e`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: consider adding a `--dry-run` summary for prune operations in human output mode.

### 2026-02-09: Add `--output` for JSON-producing commands
- Decision: Added `--output` + `--force` for `doctor`, `list`, and `scan` when `--json` is enabled to write machine-readable output to a file without shell redirects.
- Why: Automation and scripts frequently need stable JSON artifacts; file output avoids fragile redirect logic and makes pipelines more explicit.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`, `README.md`.
- Commit: `d18d4d3`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: consider adding `--output` parity to other JSON-producing commands (`info`, `version`, `init`, etc.).

### 2026-02-09: Enforce config policy guardrails at create-time
- Decision: Added `allowed_providers` and `name_pattern` fields in `config.json` and enforced them in `create` before key generation.
- Why: Teams need policy-level control for provider usage and naming; enforcing before shelling out prevents invalid key creation attempts.
- Evidence: `src/secretive_x/config.py`, `src/secretive_x/cli.py`, `tests/test_config.py`, `tests/test_cli.py`.
- Commit: `c94bf28`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: add policy profiles/presets for environment-specific rollout.

### 2026-02-09: Treat manifest file paths as untrusted input
- Decision: Added key-dir boundary checks for manifest-derived key paths in `read_public_key` and `delete_key`.
- Why: A tampered manifest could previously point to arbitrary filesystem paths for read/delete operations.
- Evidence: `src/secretive_x/core.py`, `tests/test_core.py`, `tests/test_cli.py`.
- Commit: `c94bf28`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: add optional repair command to quarantine invalid manifest entries.

### 2026-02-09: Expand CI compatibility coverage and keep a CLI smoke path
- Decision: Switched CI `check` to Python matrix (`3.11`, `3.13`) and added `make smoke` non-destructive runtime checks.
- Why: Prior regressions were Python-minor-specific; smoke checks validate command wiring in realistic process execution.
- Evidence: `.github/workflows/ci.yml`, `Makefile`, run `https://github.com/sarveshkapre/secretive-x/actions/runs/21809972093`.
- Commit: `c94bf28`.
- Confidence: high.
- Trust label: verified-github-actions.
- Follow-ups: evaluate adding an OS matrix after TPM/Secure Enclave providers land.

### 2026-02-09: Make `make check` work immediately after `make setup`
- Decision: Updated `Makefile` to prefer `.venv/bin/*` tools when a local venv exists.
- Why: Reduces dev/CI parity issues and prevents confusing “tool not found” failures when deps are installed only in `.venv`.
- Evidence: `Makefile`, `README.md`, `docs/PROJECT.md`.
- Commit: `5a9dc1f`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: consider adding a short “Getting started” section in `docs/PROJECT.md` for contributors without GNU make.

### 2026-02-09: Add `create` preflight checks for `ssh-keygen` and FIDO2 support
- Decision: `create` now checks for `ssh-keygen` on PATH and (when detectable) rejects FIDO2 creation if OpenSSH doesn’t advertise `sk-ssh-ed25519@openssh.com`; it also rejects provider-incompatible flags.
- Why: Avoids prompting users for inputs or running partial flows before failing with opaque OpenSSH errors.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`.
- Commit: `ca5cb61`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: add a provider-specific preflight command (or `doctor --strict`) once Secure Enclave / TPM providers exist.

### 2026-02-09: Report manifest/key-dir drift in `doctor`
- Decision: `doctor` now reports drift between manifest entries and on-disk key pairs, and treats invalid manifest paths (outside key dir) as unhealthy.
- Why: Drift is common during manual file edits/cleanup; surfacing it early helps keep the manifest auditable and prevents confusing “missing file” failures later.
- Evidence: `src/secretive_x/cli.py`, `src/secretive_x/core.py`, `tests/test_cli.py`.
- Commit: `ae2f951`.
- Confidence: medium-high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: ship a non-destructive `scan` reconciliation command to help resolve drift safely.

### 2026-02-09: Add `scan` drift reconciliation command
- Decision: Added `scan` to detect drift between manifest and key dir, and optionally import untracked on-disk keypairs into the manifest (`scan --apply`).
- Why: `doctor` can highlight drift, but users need a safe, non-destructive way to reconcile common “manifest missing entries” cases without hand-editing JSON.
- Evidence: `src/secretive_x/cli.py`, `tests/test_cli.py`, `README.md`.
- Commit: `34d59cc`.
- Confidence: high.
- Trust label: verified-local-tests-and-ci.
- Follow-ups: consider adding an explicit `--prune-missing` mode for cleaning manifest entries that reference missing files.

### 2026-02-09: Add OS-matrix CI smoke and best-effort secure permissions
- Decision: Added `smoke-os` CI job (ubuntu/macos/windows) using a cross-platform script, and hardened atomic writes with best-effort POSIX permissions (`0600` files, `0700` dirs).
- Why: Cross-platform runtime drift is common for CLIs; a lightweight OS-matrix smoke catches import/env/platformdirs issues early without requiring full `make check` parity on Windows.
- Evidence: `scripts/smoke_cli.py`, `.github/workflows/ci.yml`, `src/secretive_x/utils.py`, run `https://github.com/sarveshkapre/secretive-x/actions/runs/21827476179`.
- Commit: `0f24a16`.
- Confidence: high.
- Trust label: verified-github-actions.
- Follow-ups: evaluate expanding OS coverage beyond smoke once Windows-compatible equivalents of `make check` targets exist.

## Verification Evidence
- `make check` (pass; 2026-02-10 local run)
- `make smoke` (pass; 2026-02-10 local run)
- `gh run view 21860647350 --json conclusion,status,headSha,url` (pass; conclusion: success)
- `gh run watch 21836306296 --exit-status` (pass; ci workflow on `main`)
- `gh run watch 21836488654 --exit-status` (pass; ci workflow on `main`)
- `gh run watch 21836608234 --exit-status` (pass; ci workflow on `main`)
- `PYTHONPATH=src .venv/bin/python scripts/smoke_cli.py` (pass)
- `gh run view 21819876084 --json conclusion,status,headSha,url` (pass; conclusion: success)
- `gh run watch 21819955705 --exit-status` (pass; ci workflow on `main`)
- `gh run watch 21827476179 --exit-status` (pass; ci workflow on `main`)
- `gh run watch 21827544437 --exit-status` (pass; ci workflow on `main`)
