# SPDX-License-Identifier: MIT
"""Locks for origin table, hook adder table, and Pattern compile-at-bind."""

from dataclasses import dataclass

from ux_valio import Validator
from ux_valio.validators.hooks import HookHost, _HOOK_ADDERS
from ux_valio.validators.leaves import PatternValidator, _ORIGIN_CHECKERS, is_instance_of


def test_origin_table_owns_stdlib_generics():
    assert is_instance_of([1, 2], list[int]) is True
    assert is_instance_of([1, "a"], list[int]) is False
    assert is_instance_of({"a": 1}, dict[str, int]) is True
    assert is_instance_of((1, 2), tuple[int, ...]) is True
    assert list in _ORIGIN_CHECKERS
    assert dict in _ORIGIN_CHECKERS


def test_hook_taught_names_come_from_one_table():
    names = {name for name, _, _ in _HOOK_ADDERS}
    assert "add_pre_validator" in names
    assert "add_pre_validator_task" in names
    assert "add_pre_set" not in names
    assert not hasattr(HookHost, "add_pre_set")
    assert hasattr(HookHost, "add_pre_validator")
    assert hasattr(HookHost, "_add")


def test_pattern_compile_is_cached_on_owner():
    field = PatternValidator(pattern=r"ab+", name="code")
    field._validate_pattern(None, "abb")
    first = field._compiled
    field._validate_pattern(None, "abbb")
    assert field._compiled is first


def test_facade_pattern_path_uses_owner_cache():
    @dataclass
    class Row:
        sku: str = Validator(pattern=r"[A-Z]{3}", debug=True)

    Row(sku="ABC")
    desc = Row.__dict__["sku"]
    assert desc._compiled is not None
    compiled = desc._compiled
    Row(sku="XYZ")
    assert desc._compiled is compiled
