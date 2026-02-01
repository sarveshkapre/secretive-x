# AGENTS

## Purpose
This repo builds Secretive-X, a cross-platform CLI for managing non-exportable SSH keys.

## Guardrails
- Keep the scope tight: hardware-backed SSH keys and local inventory.
- No auth/account systems.
- Prefer small, auditable changes with tests.
- Do not add network calls unless required for functionality.

## Commands
All commands are documented in `docs/PROJECT.md`.

## Conventions
- Python 3.11+
- Source in `src/secretive_x`
- Tests in `tests/`
- Keep outputs CLI-friendly and deterministic.
