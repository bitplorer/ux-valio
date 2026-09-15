# SPDX-License-Identifier: MIT
"""Product surface does not teach ceremony labels as public names."""

from pathlib import Path

import ux_valio

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_GLOBS = (
    "ux_valio/**/*.py",
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
)
# Concatenated so this lock file is not itself a teaching surface.
_TOKENS = (
    "Soft" + " LOCK",
    "Soft" + " DO",
    "Soft" + " 5 Door",
    "Soft" + " #",
    "Soft" + " N",
    "_soft" + "5_",
)


def test_product_tree_has_no_soft_ceremony_tokens():
    hits = []
    for glob in PRODUCT_GLOBS:
        for path in ROOT.glob(glob):
            if not path.is_file():
                continue
            text = path.read_text()
            for token in _TOKENS:
                if token in text:
                    hits.append(f"{path.relative_to(ROOT)}: {token}")
    assert hits == []


def test_check_functions_are_not_owned_public_api():
    assert "check_length" not in ux_valio.__all__
    assert "check_value" not in ux_valio.__all__
    assert "check_type" not in ux_valio.__all__
    assert "check_instance" not in ux_valio.__all__
    assert not hasattr(ux_valio, "check_length")
    assert not hasattr(ux_valio, "check_instance")
    assert not hasattr(ux_valio.validators, "check_length")
    assert not hasattr(ux_valio.validators, "check_instance")
    assert "ListValidator" not in ux_valio.__all__
    assert not hasattr(ux_valio, "ListValidator")


def test_min_max_leaves_are_exported():
    for name in (
        "MinLengthValidator",
        "MaxLengthValidator",
        "MinValueValidator",
        "MaxValueValidator",
        "AllOf",
        "AnyOf",
        "Chain",
        "FloatValidator",
        "EmailValidator",
        "UUIDValidator",
        "PaymentCardValidator",
        "ExpiryValidator",
    ):
        assert name in ux_valio.__all__
        assert hasattr(ux_valio, name)


def test_hex_color_is_not_a_public_facade():
    assert "HexColorValidator" not in ux_valio.__all__
    assert not hasattr(ux_valio, "HexColorValidator")
    assert not hasattr(ux_valio.validators, "HexColorValidator")


def test_product_does_not_import_pyparsing():
    import ast

    hits = []
    for path in ROOT.glob("ux_valio/**/*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "pyparsing" or alias.name.startswith("pyparsing."):
                        hits.append(f"{path.relative_to(ROOT)}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "pyparsing" or node.module.startswith("pyparsing."):
                    hits.append(f"{path.relative_to(ROOT)}: from {node.module}")
    assert hits == []


def test_no_process_pack_docs_in_tree():
    docs = ROOT / "docs"
    assert not docs.exists() or not any(docs.glob("soft*.md"))


def test_validators_package_all_does_not_leak_past_top():
    leaked = set(ux_valio.validators.__all__) - set(ux_valio.__all__)
    assert leaked == set()


def test_export_floor_and_validation_errors():
    for name in ("Property", "ValidateProperty", "Validator", "ValidationErrors"):
        assert name in ux_valio.__all__
        assert hasattr(ux_valio, name)
