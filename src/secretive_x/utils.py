from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_POSIX = os.name == "posix"


def best_effort_chmod(path: Path, mode: int) -> None:
    if not _POSIX:
        return
    try:
        os.chmod(path, mode)
    except OSError:
        # Best-effort: permissions are a safety improvement but must not break the CLI.
        return


def validate_name(name: str) -> str:
    if not NAME_PATTERN.match(name):
        raise ValueError(
            "Invalid name. Use 1-64 chars: letters, numbers, dot, underscore, dash."
        )
    if os.path.sep in name or (os.path.altsep and os.path.altsep in name):
        raise ValueError("Name cannot contain path separators.")
    return name


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best_effort_chmod(path.parent, 0o700)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        json.dump(payload, tmp, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    best_effort_chmod(path, 0o600)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best_effort_chmod(path.parent, 0o700)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
    best_effort_chmod(path, 0o600)
