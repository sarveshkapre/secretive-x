from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


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
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        json.dump(payload, tmp, indent=2, sort_keys=True)
        tmp.write("\n")
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)
