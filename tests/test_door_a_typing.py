# SPDX-License-Identifier: MIT
"""Type checkers: ``name: str = StringValidator()`` is the store type."""

from pathlib import Path
import os
import subprocess
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_STR = Path(__file__).resolve().parent / "typing" / "door_a_str.py"
_DESC = Path(__file__).resolve().parent / "typing" / "door_a_user.py"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_ROOT)
    return env


def _mypy(sample: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            str(sample),
            "--python-version",
            "3.14",
            "--show-error-codes",
            "--config-file",
            str(_ROOT / "pyproject.toml"),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
        cwd=_ROOT,
    )


def _pyright(sample: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["pyright", str(sample)],
            check=False,
            capture_output=True,
            text=True,
            env=_env(),
            cwd=_ROOT,
        )
    except FileNotFoundError:
        return None


def test_mypy_accepts_str_field_annotation():
    proc = _mypy(_STR)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_mypy_accepts_descriptor_field_annotation():
    proc = _mypy(_DESC)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_pyright_accepts_str_field_annotation():
    pyright = _pyright(_STR)
    if pyright is None or pyright.returncode == 127:
        pytest.skip("pyright not installed")
    assert pyright.returncode == 0, pyright.stdout + pyright.stderr


def test_pyright_accepts_descriptor_field_annotation():
    pyright = _pyright(_DESC)
    if pyright is None or pyright.returncode == 127:
        pytest.skip("pyright not installed")
    assert pyright.returncode == 0, pyright.stdout + pyright.stderr
