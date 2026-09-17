# SPDX-License-Identifier: MIT
"""Door A README shape and Surface Lock."""

from dataclasses import dataclass

import pytest

import ux_valio
from ux_valio import IntegerValidator, StringValidator, Validator


def test_string_validator_readme_max_length_happy_path():
    @dataclass
    class User:
        name: str = StringValidator(debug=True, max_length=50, required=True)

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError):
        User(name="x" * 51)


def test_string_validator_required_none_raises_when_debug():
    @dataclass
    class User:
        name: str = StringValidator(debug=True, required=True)

    with pytest.raises(ValueError):
        User(name=None)


def test_validator_in_choice_readme_shape():
    @dataclass
    class Picked:
        s: str = Validator(in_choice=["Male", "Female", "Trans"], debug=True)

    assert Picked(s="Female").s == "Female"
    with pytest.raises(ValueError):
        Picked(s="Other")


def test_validator_in_choice_with_default_female():
    @dataclass
    class User:
        gender: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")

    assert User().gender == "Female"


def test_integer_validator_value_and_multiple_keep():
    @dataclass
    class Count:
        n: int = IntegerValidator(
            min_value=0, max_value=10, multiple_of=2, debug=True
        )

    assert Count(n=0).n == 0
    assert Count(n=10).n == 10
    with pytest.raises(ValueError):
        Count(n=-2)
    with pytest.raises(ValueError):
        Count(n=3)


def test_validator_facade_accepts_value_and_length_kwargs():
    @dataclass
    class Sized:
        s: str = Validator(min_length=0, max_length=3, debug=True)

    assert Sized(s="A").s == "A"
    assert Sized(s="").s == ""
    with pytest.raises(ValueError):
        Sized(s="abcd")

    @dataclass
    class Ranked:
        s: str = Validator(min_value="A", max_value="Z", debug=True)

    assert Ranked(s="A").s == "A"
    with pytest.raises(ValueError):
        Ranked(s="0")


def test_string_validator_min_value_override_still_runs():
    @dataclass
    class Ranked:
        name: str = StringValidator(min_value="B", debug=True)

    assert Ranked(name="Cat").name == "Cat"
    with pytest.raises(ValueError):
        Ranked(name="Ace")


def test_debug_falsy_swallows_and_readback_is_none():
    @dataclass
    class Typed:
        n: int = IntegerValidator(debug=False)

    assert Typed(n="nope").n is None


def test_debug_true_raises_type_error():
    @dataclass
    class Typed:
        n: int = IntegerValidator(debug=True)

    with pytest.raises(TypeError):
        Typed(n="nope")


def test_logger_defaults_off():
    v = Validator()
    assert v.logger is False
    i = IntegerValidator(debug=True)
    assert i.logger is False


def test_public_all_is_explicit_and_small():
    assert "Field" not in ux_valio.__all__
    assert "Schema" not in ux_valio.__all__
    assert "Validator" in ux_valio.__all__
    assert "StringValidator" in ux_valio.__all__
    assert "AllOf" in ux_valio.__all__
    assert "ValidationErrors" in ux_valio.__all__
    assert "MinLengthValidator" in ux_valio.__all__
    assert len(ux_valio.__all__) < 55


def test_no_field_schema_cap_on_package():
    assert not hasattr(ux_valio, "Field")
    assert not hasattr(ux_valio, "Schema")
    assert not hasattr(ux_valio, "Cap")
    assert not hasattr(ux_valio, "StringField")


def test_readme_teaches_facade_primary_and_chain_is_allof():
    from pathlib import Path

    text = Path(__file__).resolve().parents[1].joinpath("README.md").read_text()
    assert "Do not use bare `Property` as the field default" in text
    assert "`Chain` is `AllOf`" in text
    assert "findall substring" in text
    assert "cache_task=" in text
    assert "`PhoneNumberValidator` is a Door A string facade" in text
    assert "List / dictionary / set / tuple collection facades are not" in text
    assert 'region="IN"' in text
    assert "2 January 2020" in text
    assert "`Cls.field is not set`" in text
    assert "`default_factory=`" in text
    assert "not a Field twin" in text
