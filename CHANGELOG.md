# CHANGELOG

## Unreleased
- Add a confirmation prompt to `delete` (with `--yes/-y` to skip).
- Improve `doctor` output by reporting FIDO2 key type support and local config/manifest health when detectable.
- Add `--json` output mode to `doctor`, `list`, and `info` for automation.
- Add actionable errors for malformed config/manifest files (instead of stack traces).
- Pin Click to a Typer-compatible version and add a `--help` smoke test.

## 0.1.0
- Initial scaffolding and CLI MVP.
