# SPDX-License-Identifier: MIT
"""Examples stay importable Door A scripts (no Field / Schema / Cap)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples"


def test_examples_readme_lists_files():
    text = (EXAMPLE_DIR / "README.md").read_text()
    assert "Field twin" in text
    assert "user_account.py" in text
    assert "sku_codes.py" in text
    assert "lookaround_units.py" in text


@pytest.mark.parametrize(
    "modname",
    [
        "user_account",
        "registration",
        "checkout",
        "indian_kyc",
        "dates_paths",
        "sku_codes",
        "lookaround_units",
        "compose_hooks",
        "collect_all_form",
    ],
)
def test_example_main_runs(modname):
    import importlib

    module = importlib.import_module(f"examples.{modname}")
    assert callable(module.main)
    module.main()


def test_examples_are_not_a_second_product_door():
    import ux_valio

    assert "examples" not in ux_valio.__all__
    assert not hasattr(ux_valio, "Field")
    assert not hasattr(ux_valio, "Schema")
    assert not hasattr(ux_valio, "ListValidator")
