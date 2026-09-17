# SPDX-License-Identifier: MIT
"""Examples stay importable Door A scripts (no Field / Schema / Cap)."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples"
EXAMPLE_MODULES = (
    "user_account",
    "registration",
    "checkout",
    "indian_kyc",
    "dates_paths",
    "sku_codes",
    "lookaround_units",
    "compose_hooks",
    "collect_all_form",
)


def test_examples_readme_lists_files():
    text = (EXAMPLE_DIR / "README.md").read_text()
    assert "Field twin" in text
    assert "python examples/" in text
    for name in EXAMPLE_MODULES:
        assert f"{name}.py" in text


@pytest.mark.parametrize("modname", EXAMPLE_MODULES)
def test_example_main_runs(modname):
    import importlib

    module = importlib.import_module(f"examples.{modname}")
    assert callable(module.main)
    module.main()


@pytest.mark.parametrize("modname", EXAMPLE_MODULES)
def test_example_files_do_not_import_pytest(modname):
    path = EXAMPLE_DIR / f"{modname}.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest" or alias.name.startswith("pytest."):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "pytest" or node.module.startswith("pytest."):
                hits.append(node.module)
    assert hits == []


def test_examples_are_not_a_second_product_door():
    import ux_valio

    assert "examples" not in ux_valio.__all__
    assert not hasattr(ux_valio, "Field")
    assert not hasattr(ux_valio, "Schema")
    assert not hasattr(ux_valio, "ListValidator")
