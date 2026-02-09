# INCIDENTS

## 2026-02-01: CI failures on Python 3.11 due Typer type annotation support
- Status: resolved.
- Impact: `ci/check` failed repeatedly (runs including `21558119420`) and blocked reliable validation on `main`.
- Root cause: CLI option annotations used `str | None` unions that the pinned Typer path on Python 3.11 could not parse.
- Detection: GitHub Actions `check` logs with `RuntimeError: Type not yet supported: str | None`.
- Resolution: Reworked affected CLI option annotations to Typer-compatible forms and added command-help regression coverage.
- Prevention rules:
  - Keep CI on at least two Python minors to detect annotation/runtime drift early.
  - Add smoke/help-path tests whenever command signatures change.
  - Treat old failed CI runs as historical context, but prioritize fixing root causes on current `main`.
- Evidence: runs `21558119420` (failure), `21809972093` (post-hardening success).

## 2026-02-09 session note
- No new production regressions introduced in this session.
