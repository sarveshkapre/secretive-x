from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(cmd: list[str], *, env: dict[str, str]) -> None:
    proc = subprocess.run(cmd, env=env, text=True, capture_output=True, check=False)  # nosec
    if proc.returncode != 0:
        raise RuntimeError(
            "Smoke command failed:\n"
            f"  cmd: {' '.join(cmd)}\n"
            f"  exit: {proc.returncode}\n"
            f"  stdout:\n{proc.stdout}\n"
            f"  stderr:\n{proc.stderr}\n"
        )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    python = sys.executable

    with tempfile.TemporaryDirectory() as tmp_home, tempfile.TemporaryDirectory() as tmp_cfg:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root / "src")

        # Cross-platform isolation: Path.home() and platformdirs depend on these.
        env["HOME"] = tmp_home
        env["USERPROFILE"] = tmp_home
        env["XDG_CONFIG_HOME"] = tmp_cfg
        env["APPDATA"] = tmp_cfg
        env["LOCALAPPDATA"] = tmp_cfg

        base = [python, "-m", "secretive_x.cli"]
        out_dir = Path(tmp_cfg) / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        _run(base + ["--help"], env=env)
        _run(base + ["init", "--json"], env=env)
        _run(base + ["version", "--json"], env=env)
        _run(base + ["info", "--json"], env=env)
        _run(base + ["list", "--json"], env=env)
        _run(base + ["scan", "--json"], env=env)
        _run(base + ["resident-import", "--help"], env=env)
        _run(
            base + ["export", "--format", "json", "--output", str(out_dir / "keys.json")],
            env=env,
        )
        _run(
            base + ["export", "--format", "csv", "--output", str(out_dir / "keys.csv")],
            env=env,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
