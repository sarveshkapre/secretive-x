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

## 2026-02-09: Bandit security gate failed on `assert` in runtime code
- Status: resolved.
- Impact: `make check` failed at `bandit` during local verification.
- Root cause: `assert` was used in non-test code (`doctor` drift block), triggering Bandit `B101`.
- Detection: `make check` output flagged `src/secretive_x/cli.py` with `B101:assert_used`.
- Resolution: Removed `assert` and used a defensive local default (`records = manifest_records or {}`).
- Prevention rules:
  - Avoid `assert` in runtime code; prefer explicit checks/defaults.
  - Run `make check` before committing to catch security-gate regressions early.

### 2026-02-12T20:01:04Z | Codex execution failure
- Date: 2026-02-12T20:01:04Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-2.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:04:34Z | Codex execution failure
- Date: 2026-02-12T20:04:34Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-3.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:08:01Z | Codex execution failure
- Date: 2026-02-12T20:08:01Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-4.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:11:31Z | Codex execution failure
- Date: 2026-02-12T20:11:31Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-5.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:15:00Z | Codex execution failure
- Date: 2026-02-12T20:15:00Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-6.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:18:29Z | Codex execution failure
- Date: 2026-02-12T20:18:29Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-7.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:21:55Z | Codex execution failure
- Date: 2026-02-12T20:21:55Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-8.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:25:23Z | Codex execution failure
- Date: 2026-02-12T20:25:23Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-9.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:29:05Z | Codex execution failure
- Date: 2026-02-12T20:29:05Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-10.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:32:33Z | Codex execution failure
- Date: 2026-02-12T20:32:33Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-11.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:36:01Z | Codex execution failure
- Date: 2026-02-12T20:36:01Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-12.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:39:28Z | Codex execution failure
- Date: 2026-02-12T20:39:28Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-13.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:42:58Z | Codex execution failure
- Date: 2026-02-12T20:42:58Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-14.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:46:30Z | Codex execution failure
- Date: 2026-02-12T20:46:30Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-15.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:50:00Z | Codex execution failure
- Date: 2026-02-12T20:50:00Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-16.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:53:30Z | Codex execution failure
- Date: 2026-02-12T20:53:30Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-17.log
- Commit: pending
- Confidence: medium

### 2026-02-12T20:57:05Z | Codex execution failure
- Date: 2026-02-12T20:57:05Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-18.log
- Commit: pending
- Confidence: medium

### 2026-02-12T21:00:35Z | Codex execution failure
- Date: 2026-02-12T21:00:35Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-19.log
- Commit: pending
- Confidence: medium

### 2026-02-12T21:03:59Z | Codex execution failure
- Date: 2026-02-12T21:03:59Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-20.log
- Commit: pending
- Confidence: medium

### 2026-02-12T21:07:30Z | Codex execution failure
- Date: 2026-02-12T21:07:30Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-21.log
- Commit: pending
- Confidence: medium

### 2026-02-12T21:11:00Z | Codex execution failure
- Date: 2026-02-12T21:11:00Z
- Trigger: Codex execution failure
- Impact: Repo session did not complete cleanly
- Root Cause: codex exec returned a non-zero status
- Fix: Captured failure logs and kept repository in a recoverable state
- Prevention Rule: Re-run with same pass context and inspect pass log before retrying
- Evidence: pass_log=logs/20260212-101456-secretive-x-cycle-22.log
- Commit: pending
- Confidence: medium
