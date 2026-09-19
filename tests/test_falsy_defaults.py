# SPDX-License-Identifier: MIT
"""Assigned 0 / False / '' must not be replaced by default."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    BooleanValidator,
    IntegerValidator,
    LengthValidator,
    RequiredValidator,
    StringValidator,
    Validator,
)


def test_zero_is_not_replaced_by_integer_default():
    @dataclass
    class N:
        n: int = IntegerValidator(default=5, debug=True)

    assert N(n=0).n == 0
    assert N().n == 5
    assert N(n=None).n == 5


def test_false_is_not_replaced_by_boolean_default():
    @dataclass
    class B:
        flag: bool = BooleanValidator(default=True, debug=True)

    assert B(flag=False).flag is False
    assert B().flag is True
    assert B(flag=None).flag is True


def test_empty_string_is_not_replaced_by_string_default():
    @dataclass
    class S:
        s: str = StringValidator(default="fallback", debug=True)

    assert S(s="").s == ""
    assert S().s == "fallback"
    assert S(s=None).s == "fallback"


def test_callable_default_runs_only_for_none():
    @dataclass
    class N:
        n: int = Validator(default=lambda: 7, debug=True)

    assert N().n == 7
    assert N(n=0).n == 0


def test_property_class_get_returns_the_descriptor():
    """Class access is the descriptor so ``Cls.n.process_*`` hangs after bind.

    Dataclass ``getattr`` then sees the descriptor as the default; ``__set__``
    treats that identity as unset and applies ``default``.
    """
    field = IntegerValidator(default=5, debug=True)

    @dataclass
    class N:
        n: int = field

    assert N.n is field
    assert N().n == 5
    n = N()
    n.n = N.n
    assert n.n == 5


def test_mutable_list_default_is_shared_across_instances():
    field = Validator(default=[], debug=True)

    @dataclass
    class Box:
        items: list = field

    first = Box()
    second = Box()
    first.items.append(1)
    assert second.items == [1]
    assert first.items is second.items


def test_default_factory_list_is_per_instance():
    field = Validator(default_factory=list, debug=True)

    @dataclass
    class Box:
        items: list = field

    first = Box()
    second = Box()
    first.items.append(1)
    assert first.items == [1]
    assert second.items == []
    assert first.items is not second.items


def test_default_and_default_factory_together_are_type_error():
    with pytest.raises(TypeError, match="cannot both be set"):
        Validator(default=[], default_factory=list)


def test_non_callable_default_factory_is_type_error():
    with pytest.raises(TypeError, match="callable"):
        Validator(default_factory=[])


def test_callable_default_list_type_still_invokes():
    """leftover: valio callable default= is still invoked; prefer default_factory."""

    @dataclass
    class Box:
        items: list = Validator(default=list, debug=True)

    first = Box()
    second = Box()
    first.items.append(1)
    assert second.items == []


def test_right_default_factory_is_not_discarded():
    field = LengthValidator(min_length=0) & RequiredValidator(
        required=False, default_factory=list
    )
    assert field.default_factory is list


def test_conflicting_default_factory_fails_closed():
    with pytest.raises(TypeError, match="conflicting default_factory"):
        LengthValidator(min_length=0, default_factory=list) & RequiredValidator(
            required=False, default_factory=dict
        )


def test_default_and_default_factory_on_compose_members_fail_closed():
    with pytest.raises(TypeError, match="cannot both be set"):
        LengthValidator(min_length=0, default=[]) & RequiredValidator(
            required=False, default_factory=list
        )
