from pathlib import Path

import pytest

from secretive_x.utils import atomic_write_json, atomic_write_text, validate_name


def test_validate_name_ok() -> None:
    assert validate_name("work-laptop") == "work-laptop"
    assert validate_name("work_1") == "work_1"
    assert validate_name("work.1") == "work.1"


def test_validate_name_bad() -> None:
    with pytest.raises(ValueError):
        validate_name("../oops")
    with pytest.raises(ValueError):
        validate_name("spaces not allowed")
    with pytest.raises(ValueError):
        validate_name("")


def test_atomic_write_json(tmp_path: Path) -> None:
    target = tmp_path / "data.json"
    atomic_write_json(target, {"hello": "world"})
    assert target.exists()
    assert target.read_text().strip().startswith("{")


def test_atomic_write_text(tmp_path: Path) -> None:
    target = tmp_path / "note.txt"
    atomic_write_text(target, "hello\n")
    assert target.exists()
    assert target.read_text() == "hello\n"


def test_atomic_write_sets_secure_permissions_on_posix(tmp_path: Path) -> None:
    import os

    if os.name != "posix":
        return

    a_dir = tmp_path / "a"
    a_dir.mkdir()
    os.chmod(a_dir, 0o755)

    target = a_dir / "b" / "note.txt"
    atomic_write_text(target, "hello\n")
    assert (target.stat().st_mode & 0o777) == 0o600
    assert (target.parent.stat().st_mode & 0o777) == 0o700
