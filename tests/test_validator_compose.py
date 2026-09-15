# SPDX-License-Identifier: MIT
"""Validator objects compose with each other as one Door A descriptor.

Inheritance hygiene (facades do not subclass leaves) is a separate lock.
"""

from dataclasses import dataclass

import pytest

from ux_valio import (
    AllOf,
    AnyOf,
    Chain,
    IntegerValidator,
    LengthValidator,
    PatternValidator,
    RequiredValidator,
    StringValidator,
    ValidateProperty,
    Validator,
)


def test_length_and_required_as_one_field_default():
    field = LengthValidator(min_length=3, debug=True) & RequiredValidator(required=True)
    assert isinstance(field, AllOf)
    assert isinstance(field, ValidateProperty)

    @dataclass
    class User:
        name: str = field

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError, match="minimum length"):
        User(name="Ab")
    with pytest.raises(ValueError, match="requires value"):
        User(name=None)


def test_allof_length_required_explicit():
    field = AllOf(
        LengthValidator(min_length=3, debug=True),
        RequiredValidator(required=True),
    )

    @dataclass
    class User:
        name: str = field

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError):
        User(name="Ab")
    with pytest.raises(ValueError):
        User(name=None)


def test_chain_is_ordered_allof():
    assert Chain is AllOf
    field = Chain(
        LengthValidator(min_length=2, debug=True),
        RequiredValidator(required=True),
    )
    assert isinstance(field, AllOf)
    assert type(field) is AllOf

    @dataclass
    class Token:
        s: str = field

    assert Token(s="ok").s == "ok"
    with pytest.raises(ValueError):
        Token(s="x")


def test_and_flattens_nested_allof():
    composed = (
        LengthValidator(min_length=1, debug=True)
        & RequiredValidator(required=True)
        & LengthValidator(max_length=5, debug=True)
    )
    assert type(composed) is AllOf
    assert len(composed.validators) == 3


def test_anyof_pattern_alternatives():
    field = PatternValidator(pattern=r"cat", debug=True) | PatternValidator(pattern=r"dog")
    assert isinstance(field, AnyOf)

    @dataclass
    class Pet:
        value: str = field

    assert Pet(value="a cat here").value == "a cat here"
    assert Pet(value="doggo").value == "doggo"
    with pytest.raises(ValueError, match="none of the alternatives"):
        Pet(value="bird")


def test_compose_facade_with_leaf():
    field = StringValidator(debug=True, max_length=8) & RequiredValidator(required=True)

    @dataclass
    class User:
        name: str = field

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError):
        User(name="abcdefghijk")
    with pytest.raises(ValueError):
        User(name=None)


def test_integer_and_multiple_still_one_descriptor():
    field = IntegerValidator(debug=True, min_value=0) & RequiredValidator(required=True)

    @dataclass
    class Count:
        n: int = field

    assert Count(n=2).n == 2
    with pytest.raises(ValueError):
        Count(n=-1)


def test_compose_does_not_multiple_inherit_leaves():
    field = LengthValidator(min_length=1) & RequiredValidator(required=True)
    assert not issubclass(type(field), LengthValidator)
    assert not issubclass(type(field), RequiredValidator)
    assert type(field).__bases__[0].__name__ != "LengthValidator"
    assert issubclass(type(field), ValidateProperty)
    assert not issubclass(Validator, AllOf)


def test_conflicting_typed_facades_fail_at_compose():
    with pytest.raises(TypeError, match="conflicting annotations"):
        IntegerValidator(debug=True) & StringValidator(debug=True)


def test_allof_and_requires_validators():
    with pytest.raises(TypeError):
        LengthValidator(min_length=1) & "nope"
    with pytest.raises(TypeError):
        AllOf(LengthValidator(min_length=1))
