# Clone Feature Tracker

## Context Sources
- README and docs
- TODO/FIXME markers in code
- Test and build failures
- Gaps found during codebase exploration
- GitHub Actions failure runs (`ci` workflow)

## Candidate Features To Do
- [ ] P0 Add config policy guardrails (`allowed_providers`, `name_pattern`) and enforce them in `create`.
- [ ] P0 Harden manifest-derived file paths so `pubkey`/`delete` refuse paths outside configured key dir.
- [ ] P1 Add regression tests for policy guardrails and tampered-manifest path handling.
- [ ] P1 Expand CI to a Python matrix (`3.11` + `3.13`) for earlier compatibility detection.
- [ ] P1 Add a local non-destructive smoke verification path for core CLI commands.
- [ ] P2 Add and maintain `PROJECT_MEMORY.md` + `INCIDENTS.md` with structured session evidence.

## Implemented
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
- [x] 2026-02-09: Synced product memory/docs for new behavior and verification evidence.  
  Evidence: `README.md`, `PLAN.md`, `CHANGELOG.md`, `UPDATE.md`, `docs/PROJECT.md`.

## Insights
- Typer runtime compatibility can diverge across Python minors; local green runs on newer Python do not guarantee CI safety on Python 3.11.
- `gitleaks/gitleaks-action@v2` ignores unsupported `args` input and still scans git history by commit range, so shallow fetch can produce false-failure CI.
- Manifest/config schema validation needs explicit shape checks to avoid accidental stack traces from malformed user-edited JSON.

## Notes
- This file is maintained by the autonomous clone loop.
