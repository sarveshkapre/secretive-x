# Update (2026-02-09, cycle 2)

## Shipped
- Security/policy: added config-driven creation guardrails (`allowed_providers`, `name_pattern`) enforced by `create`.
- Security hardening: `pubkey` and `delete` now reject manifest paths outside configured key dir, blocking tampered manifest path traversal.
- CI reliability: expanded `check` workflow job to Python `3.11` + `3.13` matrix and validated green on both.
- Runtime validation: added `make smoke` for non-destructive isolated CLI verification (`init`, `info`, `list`, `version`).
- Test coverage: added regression tests for policy parsing/enforcement and core path-hardening behavior.

## Verification
```bash
PATH="$(pwd)/.venv/bin:$PATH" make check
tmp_home="$(mktemp -d)"; tmp_cfg="$(mktemp -d)"; \
HOME="$tmp_home" XDG_CONFIG_HOME="$tmp_cfg" PYTHONPATH=src PATH="$(pwd)/.venv/bin:$PATH" \
python3 -m secretive_x.cli init --json && \
python3 -m secretive_x.cli info --json && \
python3 -m secretive_x.cli list --json && \
python3 -m secretive_x.cli version --json
gh run watch 21809972093 --exit-status
```

# Update (2026-02-09)

## Shipped
- CI reliability: fixed GitHub Actions `gitleaks` job to fetch full git history (`fetch-depth: 0`) and removed unsupported action input arguments.
- Python 3.11 compatibility hardening: updated CLI option type annotations to avoid Typer runtime failures on optional union annotations.
- Product UX: added `list --provider` filtering and deterministic key ordering for both human and JSON output.
- Reliability: added explicit config and manifest schema validation with actionable error messages for malformed root/field shapes.
- Test coverage: added regression tests for command help parsing, provider filtering, and malformed config/manifest schema paths.

## Verification
```bash
PATH="$(pwd)/.venv/bin:$PATH" make check
```

# Update (2026-02-01)

## Shipped
- Safer deletes: `secretive-x delete <name>` now prompts for confirmation by default; use `--yes/-y` for non-interactive scripts.
- Better diagnostics: `secretive-x doctor` now reports whether the installed OpenSSH advertises FIDO2 key type support (when detectable via `ssh -Q key`).
- Compatibility fix: pin Click to a Typer-compatible version; add a smoke test to ensure `--help` doesn’t crash.
- Automation: `doctor`, `list`, and `info` support `--json` for machine-readable output.
- Reliability: malformed config/manifest now produce actionable errors (and `doctor` reports config/manifest/key dir health).
- UX/safety: `init` is now idempotent and won’t overwrite an existing config unless `--force` is passed (and `init` supports `--json`).
- Automation: `create`, `pubkey`, `ssh-config`, and `delete` now support `--json` too (and `delete --json` requires `--yes`).
- Automation: `version` command for scripts (with `--json` support).
- UX: `pubkey` and `ssh-config` support `--output` file writes (use `--force` to overwrite).

## PR
- https://github.com/sarveshkapre/secretive-x/pull/1

## Verification
```bash
make check
```

## PR instructions
If you have GitHub CLI:
```bash
git push -u origin HEAD
gh pr create --title "Safer delete + doctor FIDO2 support + Click pin" --body "Adds delete confirmation/--yes, improves doctor output, pins Click for Typer compatibility, and adds a CLI help smoke test."
```

If you don’t have `gh` configured:
```bash
git push -u origin HEAD
```
Then open a PR in the GitHub UI with the same title/body.
