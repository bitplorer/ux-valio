# SPDX-License-Identifier: MIT
"""Compose-root process_* hang; leaf stacks stay bag-free; merge fail-closed."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    AllOf,
    AnyOf,
    Chain,
    LengthValidator,
    RequiredValidator,
    StringValidator,
    Validator,
)
from ux_valio.validators.hooks import HookHost


def test_compose_root_and_leaves_have_add_star():
    field = LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True)
    assert hasattr(field, "process_pre_validate")
    assert hasattr(field, "add_validator")
    assert hasattr(field, "task_pre_validate")
    assert hasattr(LengthValidator(min_length=1), "process_pre_validate")
    assert hasattr(RequiredValidator(required=True), "add_validator")
    assert not hasattr(field, "add_pre_set")
    assert "pre_set" not in field._processors


def test_hang_after_compose_on_root():
    field = LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True)

    @dataclass
    class User:
        name: str = field

    field.process_pre_validate(
        lambda instance, value: value.strip() if isinstance(value, str) else value,
        namespace=User,
    )

    assert User(name="  Ada  ").name == "Ada"


def test_compose_does_not_copy_root_hooks_onto_members():
    left = LengthValidator(min_length=1)
    right = RequiredValidator(required=True)
    field = left & right
    assert left._processors is not field._processors
    assert right._processors is not field._processors
    assert not HookHost._has_hooks(left)
    assert not HookHost._has_hooks(right)


def test_hang_on_facade_before_compose_still_runs():
    left = StringValidator(debug=True)
    field = left & RequiredValidator(required=True)

    @dataclass
    class User:
        name: str = field

    left.process_pre_validate(
        lambda instance, value: value.strip() if isinstance(value, str) else value,
        namespace=User,
    )

    assert User(name="  Ada  ").name == "Ada"


def test_nested_compose_with_hooks_is_not_flattened():
    inner = LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True)
    inner.process_pre_validate(lambda instance, value: value, namespace="compose.User")
    outer = inner & LengthValidator(max_length=10)
    assert len(outer.validators) == 2
    assert type(outer.validators[0]) is AllOf


def test_empty_nested_allof_still_flattens():
    composed = (
        LengthValidator(min_length=1, debug=True)
        & RequiredValidator(required=True)
        & LengthValidator(max_length=5, debug=True)
    )
    assert type(composed) is AllOf
    assert len(composed.validators) == 3


def test_right_debug_true_is_not_discarded_into_swallow():
    field = LengthValidator(min_length=3) & RequiredValidator(required=True, debug=True)
    assert field.debug is True

    @dataclass
    class User:
        name: str = field

    with pytest.raises(ValueError, match="minimum length"):
        User(name="Ab")


def test_conflicting_debug_fails_closed():
    with pytest.raises(TypeError, match="conflicting debug"):
        LengthValidator(min_length=3, debug=True) & RequiredValidator(
            required=True, debug=False
        )


def test_right_default_is_not_discarded():
    field = LengthValidator(min_length=1) & RequiredValidator(
        required=True, default="Ada"
    )
    assert field.default == "Ada"


def test_conflicting_default_fails_closed():
    with pytest.raises(TypeError, match="conflicting default"):
        LengthValidator(min_length=1, default="a") & RequiredValidator(
            required=True, default="b"
        )


def test_compose_root_rejects_cache_task_kwarg():
    with pytest.raises(TypeError, match="cache_task"):
        AllOf(
            LengthValidator(min_length=1),
            RequiredValidator(required=True),
            cache_task=False,
            debug=True,
        )
    with pytest.raises(TypeError, match="cache_task"):
        AnyOf(
            LengthValidator(min_length=1),
            RequiredValidator(required=True),
            cache_task=False,
        )


def test_chain_is_allof_alias():
    assert Chain is AllOf
    field = Chain(
        LengthValidator(min_length=2, debug=True),
        RequiredValidator(required=True),
    )
    assert type(field) is AllOf

    @dataclass
    class Token:
        s: str = field

    assert Token(s="ok").s == "ok"
    with pytest.raises(ValueError):
        Token(s="x")


def test_anyof_root_also_has_add_star():
    field = StringValidator(debug=True) | RequiredValidator(required=True)
    assert isinstance(field, AnyOf)
    assert hasattr(field, "process_post_validate")
    assert not hasattr(Validator, "add_pre_set")


def test_explicit_collect_all_false_does_not_lose_to_true():
    with pytest.raises(TypeError, match="conflicting collect_all"):
        LengthValidator(min_length=1, collect_all=True) & RequiredValidator(
            required=True, collect_all=False
        )


def test_unspecified_collect_all_keeps_explicit_true():
    field = LengthValidator(min_length=1, collect_all=True) & RequiredValidator(
        required=True
    )
    assert field.collect_all is True


def test_unspecified_collect_all_keeps_explicit_false():
    field = LengthValidator(min_length=1) & RequiredValidator(
        required=True, collect_all=False
    )
    assert field.collect_all is False


def test_explicit_logger_false_does_not_lose_to_true():
    with pytest.raises(TypeError, match="conflicting logger"):
        LengthValidator(min_length=1, logger=True) & RequiredValidator(
            required=True, logger=False
        )


def test_unspecified_logger_false_keeps_explicit_true():
    field = LengthValidator(min_length=1, logger=True) & RequiredValidator(
        required=True
    )
    assert field.logger is True


def test_debug_conflict_stays_fail_closed():
    with pytest.raises(TypeError, match="conflicting debug"):
        LengthValidator(min_length=1, debug=True) & RequiredValidator(
            required=True, debug=False
        )
