# SPDX-License-Identifier: MIT
"""Locks for origin table, hook adder table, and Pattern compile-at-bind."""

from dataclasses import dataclass

from ux_valio import Validator
from ux_valio.validators.hooks import HookHost
from ux_valio.validators.leaves import PatternValidator, TypeValidator, is_instance_of


def test_origin_table_owns_stdlib_generics():
    assert is_instance_of([1, 2], list[int]) is True
    assert is_instance_of([1, "a"], list[int]) is False
    assert is_instance_of({"a": 1}, dict[str, int]) is True
    assert is_instance_of((1, 2), tuple[int, ...]) is True
    assert list in TypeValidator._ORIGIN_CHECKERS
    assert dict in TypeValidator._ORIGIN_CHECKERS


def test_hook_taught_names_come_from_one_table():
    names = {name for name, _, _ in HookHost._HOOK_ADDERS}
    assert "add_pre_validator" in names
    assert "add_pre_validator_task" in names
    assert "add_pre_set" not in names
    assert not hasattr(HookHost, "add_pre_set")
    assert hasattr(HookHost, "add_pre_validator")
    assert hasattr(HookHost, "_add")


def test_hook_and_origin_tables_live_on_owning_types():
    """Free-floating module tables are not the owner. The class is."""
    import ux_valio.validators.hooks as hooks_mod
    import ux_valio.validators.leaves as leaves_mod
    import ux_valio.validators.compose as compose_mod

    assert not hasattr(hooks_mod, "_HOOK_ADDERS")
    assert not hasattr(hooks_mod, "_PROCESSOR_PHASES")
    assert HookHost._HOOK_ADDERS[0][0] == "add_pre_validator"
    assert not hasattr(leaves_mod, "_ORIGIN_CHECKERS")
    assert not hasattr(leaves_mod, "_ORIGIN_GROUPS")
    assert list in TypeValidator._ORIGIN_CHECKERS
    assert TypeValidator._ORIGIN_GROUPS
    assert not hasattr(compose_mod, "_bind_compose_kwargs")
    assert not hasattr(compose_mod, "_flatten")
    assert hasattr(compose_mod._Compose, "_bind_kwargs")
    assert hasattr(compose_mod._Compose, "_flatten")
    assert hasattr(compose_mod._Compose, "_merged_annotation")

    import ux_valio.validators.length as length_mod
    from ux_valio.validators.length import LengthValidator

    assert LengthValidator._len_or_reject is length_mod._len_or_reject
    assert HookHost._collect_bag_keys is hooks_mod._collect_bag_keys


def test_pattern_compile_is_cached_on_owner():
    field = PatternValidator(pattern=r"ab+", name="code")
    field._validate_pattern(None, "abb")
    first = field._compiled
    field._validate_pattern(None, "abbb")
    assert field._compiled is first


def test_email_identity_reuses_compiled_finder():
    from ux_valio import EmailValidator

    field = EmailValidator(debug=True, name="email")
    field.validate(None, "user@example.com")
    first = field._compiled
    assert first is not None
    field.validate(None, "other@example.com")
    assert field._compiled is first
    assert first.fullmatch("user@example.com") is not None


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
