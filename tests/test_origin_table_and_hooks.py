# SPDX-License-Identifier: MIT
"""Locks for origin table, hook adder table, and Pattern compile-at-bind."""

from dataclasses import dataclass

from ux_valio import Validator
from ux_valio.validators.hooks import HookHost
from ux_valio.validators.leaves import (
    PatternValidator,
    TypeValidator,
    _ORIGIN_CHECKERS,
    _ORIGIN_GROUPS,
    is_instance_of,
)


def test_origin_table_owns_stdlib_generics():
    assert is_instance_of([1, 2], list[int]) is True
    assert is_instance_of([1, "a"], list[int]) is False
    assert is_instance_of({"a": 1}, dict[str, int]) is True
    assert is_instance_of((1, 2), tuple[int, ...]) is True
    assert list in _ORIGIN_CHECKERS
    assert dict in _ORIGIN_CHECKERS
    assert _ORIGIN_GROUPS


def test_hook_taught_names_come_from_one_table():
    names = {name for name, _, _ in HookHost._HOOK_ADDERS}
    assert "add_pre_validator" in names
    assert "add_pre_validator_task" in names
    assert "add_pre_set" not in names
    assert not hasattr(HookHost, "add_pre_set")
    assert hasattr(HookHost, "add_pre_validator")
    assert hasattr(HookHost, "_add")


def test_hook_tables_on_host_origin_tables_beside_is_instance_of():
    """Hook adders stay on HookHost. Origin tables sit next to is_instance_of."""
    import ux_valio.validators.hooks as hooks_mod
    import ux_valio.validators.leaves as leaves_mod
    import ux_valio.validators.compose as compose_mod
    import ux_valio.validators.length as length_mod
    from ux_valio.validators.length import LengthValidator

    assert not hasattr(hooks_mod, "_HOOK_ADDERS")
    assert not hasattr(hooks_mod, "_PROCESSOR_PHASES")
    assert HookHost._HOOK_ADDERS[0][0] == "add_pre_validator"
    assert list in leaves_mod._ORIGIN_CHECKERS
    assert leaves_mod._ORIGIN_GROUPS
    assert not hasattr(TypeValidator, "_ORIGIN_CHECKERS")
    assert not hasattr(TypeValidator, "_ORIGIN_GROUPS")
    assert not hasattr(compose_mod, "_bind_compose_kwargs")
    assert not hasattr(compose_mod, "_flatten")
    assert hasattr(compose_mod._Compose, "_bind_kwargs")
    assert hasattr(compose_mod._Compose, "_flatten")
    assert hasattr(compose_mod._Compose, "_merged_annotation")
    assert hasattr(LengthValidator, "_len_or_reject")
    assert not hasattr(length_mod, "_len_or_reject")
    assert hasattr(HookHost, "_collect_bag_keys")
    assert hasattr(HookHost, "_bag_key")
    assert hasattr(HookHost, "_resolve_bag_key")
    assert not hasattr(hooks_mod, "_collect_bag_keys")
    assert not hasattr(hooks_mod, "_bag_key")
    assert not hasattr(hooks_mod, "_resolve_bag_key")
    assert not hasattr(hooks_mod, "_hook_adder")
    from ux_valio.validators.typed import DateValidator
    import ux_valio.validators.typed as typed_mod

    assert hasattr(DateValidator, "_parse_eu_ind_date")
    assert not hasattr(typed_mod, "_parse_eu_ind_date")
    assert not hasattr(hooks_mod, "_namespace")
    assert not hasattr(hooks_mod, "hook_bags_used")


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
