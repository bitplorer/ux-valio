# SPDX-License-Identifier: MIT
"""Opt-in collect_all continues concerns. Default stays fail-fast.

collect_all is not debug-swallow: debug still chooses raise vs append.
"""

from dataclasses import dataclass

import pytest

from ux_valio import (
    AllOf,
    AnyOf,
    IntegerValidator,
    MinLengthValidator,
    PatternValidator,
    RequiredValidator,
    ValidationErrors,
    Validator,
)


def test_collect_all_defaults_false_fail_fast():
    field = IntegerValidator(min_value=0, multiple_of=2, debug=False)
    assert field.collect_all is False

    @dataclass
    class Count:
        n: int = field

    count = Count(n=-1)
    assert "n" not in count.__dict__
    assert len(field.errors) == 1
    assert "multiple of" in str(field.errors[0])


def test_debug_true_is_not_collect_all():
    field = IntegerValidator(min_value=0, multiple_of=2, debug=True)
    assert field.collect_all is False

    @dataclass
    class Count:
        n: int = field

    with pytest.raises(ValueError, match="multiple of") as caught:
        Count(n=-1)
    assert not isinstance(caught.value, ValidationErrors)


def test_collect_all_debug_true_raises_validation_errors():
    field = IntegerValidator(min_value=0, multiple_of=2, collect_all=True, debug=True)

    @dataclass
    class Count:
        n: int = field

    with pytest.raises(ValidationErrors) as caught:
        Count(n=-1)
    assert len(caught.value.errors) >= 2
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "multiple of" in messages
    assert "minimum value" in messages


def test_collect_all_debug_falsy_appends_all_and_swallows():
    field = IntegerValidator(min_value=0, multiple_of=2, collect_all=True, debug=False)

    @dataclass
    class Count:
        n: int = field

    assert Count(n=-1).n is None
    assert len(field.errors) >= 2
    assert all(not isinstance(err, ValidationErrors) for err in field.errors)


def test_collect_all_allof_continues_members():
    field = AllOf(
        MinLengthValidator(min_length=10),
        PatternValidator(pattern=r"xyz"),
        collect_all=True,
        debug=True,
    )

    @dataclass
    class Token:
        s: str = field

    with pytest.raises(ValidationErrors) as caught:
        Token(s="ab")
    assert len(caught.value.errors) >= 2


def test_collect_all_anyof_surfaces_alternative_errors():
    field = AnyOf(
        PatternValidator(pattern=r"cat"),
        PatternValidator(pattern=r"dog"),
        collect_all=True,
        debug=True,
    )

    @dataclass
    class Pet:
        value: str = field

    with pytest.raises(ValidationErrors) as caught:
        Pet(value="bird")
    assert len(caught.value.errors) >= 2


def test_anyof_default_still_one_value_error():
    field = PatternValidator(pattern=r"cat", debug=True) | PatternValidator(pattern=r"dog")

    @dataclass
    class Pet:
        value: str = field

    with pytest.raises(ValueError, match="none of the alternatives") as caught:
        Pet(value="bird")
    assert not isinstance(caught.value, ValidationErrors)


def test_collect_all_rejects_non_bool():
    with pytest.raises(TypeError, match="collect_all"):
        Validator(collect_all="yes")


def test_collect_all_on_allof_survives_further_compose():
    inner = AllOf(
        MinLengthValidator(min_length=10),
        PatternValidator(pattern=r"xyz"),
        collect_all=True,
        debug=True,
    )
    field = inner & RequiredValidator(required=True)
    assert field.collect_all is True
    assert len(field.validators) == 2


def test_collect_all_unknown_is_not_a_debug_alias():
    field = Validator(debug=True)
    assert field.collect_all is False
    assert field.debug is True
