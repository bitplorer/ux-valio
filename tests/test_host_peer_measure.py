# SPDX-License-Identifier: MIT
"""CI wire for the host/peer measure harness: skip-with-reason, never fail CI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benches" / "measure_host_peer.py"


def test_measure_harness_ci_mode_skips_or_smokes():
    """``--ci`` never builds Rust. Missing stub is SKIP (exit 0), not a red test."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--ci"],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(ROOT),
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, out
    assert "SKIP:" in out or "SMOKE:" in out, out
    assert "not Cap Door B" in out
