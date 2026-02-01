from pathlib import Path

import pytest

from secretive_x.utils import atomic_write_json, validate_name


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
