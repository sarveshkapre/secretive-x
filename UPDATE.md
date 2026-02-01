# Update (2026-02-01)

## Shipped
- Safer deletes: `secretive-x delete <name>` now prompts for confirmation by default; use `--yes/-y` for non-interactive scripts.
- Better diagnostics: `secretive-x doctor` now reports whether the installed OpenSSH advertises FIDO2 key type support (when detectable via `ssh -Q key`).
- Compatibility fix: pin Click to a Typer-compatible version; add a smoke test to ensure `--help` doesn’t crash.

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
