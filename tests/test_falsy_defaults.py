# SPDX-License-Identifier: MIT
"""Assigned 0 / False / '' must not be replaced by default."""

from dataclasses import dataclass

from ux_valio import BooleanValidator, IntegerValidator, StringValidator, Validator


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


def test_property_class_get_returns_none_so_dataclass_default_is_none():
    field = IntegerValidator(default=5, debug=True)

    @dataclass
    class N:
        n: int = field

    assert N.n is None
    assert N().n == 5
