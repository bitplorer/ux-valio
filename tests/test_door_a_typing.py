# SPDX-License-Identifier: MIT
"""Type checkers: annotate the descriptor; instance access is the store type."""

from pathlib import Path
import os
import subprocess
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SAMPLE = Path(__file__).resolve().parent / "typing" / "door_a_user.py"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_ROOT)
    return env


def test_mypy_accepts_descriptor_field_annotation():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            str(_SAMPLE),
            "--python-version",
            "3.14",
            "--show-error-codes",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_env(),
        cwd=_ROOT,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_pyright_accepts_descriptor_field_annotation():
    try:
        pyright = subprocess.run(
            ["pyright", str(_SAMPLE)],
            check=False,
            capture_output=True,
            text=True,
            env=_env(),
            cwd=_ROOT,
        )
    except FileNotFoundError:
        pytest.skip("pyright not installed")
    if pyright.returncode == 127 or "not found" in (pyright.stderr or "").lower():
        pytest.skip("pyright not installed")
    assert pyright.returncode == 0, pyright.stdout + pyright.stderr
