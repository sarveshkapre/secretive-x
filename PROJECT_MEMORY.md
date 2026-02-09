# PROJECT_MEMORY

## Decisions

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
