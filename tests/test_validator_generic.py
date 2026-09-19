# SPDX-License-Identifier: MIT
"""Validator[T] is the stored-type subscript. Not a second door.

Owner field annotation remains Door A. The subscript fills annotation when
the class did not declare one. Unconstrained TypeVars are typing-only.
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

import pytest

from ux_valio import IntegerValidator, ValidationErrors, Validator


def test_validator_int_subscript_types_a_plain_class():
    class Stats:
        n = Validator[int](min_value=0, debug=True)

    stats = Stats()
    stats.n = 3
    assert stats.n == 3
    with pytest.raises((TypeError, ValidationErrors)):
        stats.n = "x"
    assert Stats.__dict__["n"].annotation is int


def test_unbound_validator_int_validate_uses_subscript():
    field = Validator[int](debug=True, name="n")
    field.validate(None, 1)
    with pytest.raises(TypeError):
        field.validate(None, "x")
    assert field.annotation is int


def test_validator_int_agrees_with_owner_int():
    @dataclass
    class User:
        n: int = Validator[int](min_value=0, debug=True)

    assert User(n=2).n == 2
    with pytest.raises((TypeError, ValidationErrors)):
        User(n="x")


def test_validator_int_conflicts_with_owner_str():
    with pytest.raises((TypeError, RuntimeError)):
        @dataclass
        class User:
            n: str = Validator[int](debug=True)


def test_integer_validator_is_validator_int():
    assert issubclass(IntegerValidator, Validator)
    field = IntegerValidator(debug=True, name="n")
    field.validate(None, 1)
    with pytest.raises(TypeError):
        field.validate(None, "x")
    assert field.annotation is int


def test_validator_subscript_takes_one_argument():
    with pytest.raises(TypeError):
        Validator[int, str](debug=True, name="n")


def test_unconstrained_typevar_owner_is_typing_only():
    T = TypeVar("T")

    class Box(Generic[T]):
        item: T = Validator(debug=True)

    box = Box()
    box.item = 1
    assert box.item == 1
    box.item = "x"
    assert box.item == "x"
    assert Box.__dict__["item"].annotation is None


def test_bound_typevar_owner_still_checks_the_bound():
    T = TypeVar("T", bound=int)

    class Box(Generic[T]):
        item: T = Validator(debug=True)

    box = Box()
    box.item = 1
    assert box.item == 1
    with pytest.raises(TypeError):
        box.item = "x"


def test_unconstrained_typevar_subscript_is_typing_only():
    T = TypeVar("T")
    field = Validator[T](debug=True, name="item")
    field.validate(None, 1)
    field.validate(None, "x")
    assert field.annotation is None


def test_custom_store_type_needs_no_mixin():
    class Account:
        def __init__(self, id: str) -> None:
            self.id = id

    class AccountValidator(Validator[Account]):
        annotation = Account

    @dataclass
    class Row:
        owner: Account = AccountValidator()

    row = Row(owner=Account("a1"))
    assert row.owner.id == "a1"
    with pytest.raises(TypeError):
        Row(owner="a1")
