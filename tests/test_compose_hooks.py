# SPDX-License-Identifier: MIT
"""Compose-root add_* hang; leaf stacks stay bag-free; merge fail-closed."""

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


def test_compose_root_has_add_star_leaves_do_not():
    field = LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True)
    assert hasattr(field, "add_pre_validator")
    assert hasattr(field, "add_validator")
    assert hasattr(field, "add_pre_validator_task")
    assert not hasattr(LengthValidator(min_length=1), "add_pre_validator")
    assert not hasattr(RequiredValidator(required=True), "add_validator")
    assert not hasattr(field, "add_pre_set")
    assert "pre_set" not in field._processors


def test_hang_after_compose_on_root():
    field = LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True)
    field.add_pre_validator(
        lambda instance, value: value.strip() if isinstance(value, str) else value,
        namespace="User",
    )

    @dataclass
    class User:
        name: str = field

    assert User(name="  Ada  ").name == "Ada"


def test_leaf_members_stay_bag_free_after_compose():
    left = LengthValidator(min_length=1)
    right = RequiredValidator(required=True)
    field = left & right
    assert not hasattr(left, "_processors")
    assert not hasattr(right, "_processors")
    assert hasattr(field, "_processors")


def test_hang_on_facade_before_compose_still_runs():
    left = StringValidator(debug=True)
    left.add_pre_validator(
        lambda instance, value: value.strip() if isinstance(value, str) else value,
        namespace="User",
    )
    field = left & RequiredValidator(required=True)

    @dataclass
    class User:
        name: str = field

    assert User(name="  Ada  ").name == "Ada"


def test_nested_compose_with_hooks_is_not_flattened():
    inner = LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True)
    inner.add_pre_validator(lambda instance, value: value, namespace="User")
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
    assert hasattr(field, "add_post_validator")
    assert not hasattr(Validator, "add_pre_set")
