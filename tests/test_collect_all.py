# SPDX-License-Identifier: MIT
"""Opt-in collect_all continues concerns. Default stays fail-fast.

collect_all is not debug-swallow: debug still chooses raise vs append.
"""

import datetime
import pathlib
from dataclasses import dataclass

import pytest

from ux_valio import (
    AllOf,
    AnyOf,
    AadhaarCardValidator,
    DateValidator,
    ExpiryValidator,
    IntegerValidator,
    IPv4Validator,
    MinLengthValidator,
    PANCardValidator,
    PathValidator,
    PatternValidator,
    PaymentCardValidator,
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


def test_named_facade_collect_all_keeps_inherited_and_extra_errors():
    """Extra checks after the inherited path must join the collect_all bag."""
    card = PaymentCardValidator(min_length=20, collect_all=True, debug=True)
    with pytest.raises(ValidationErrors) as caught:
        card.validate(None, "4111")
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "minimum length" in messages
    assert "payment card" in messages
    assert len(caught.value.errors) >= 2

    ip = IPv4Validator(max_length=3, collect_all=True, debug=True)
    with pytest.raises(ValidationErrors) as caught_ip:
        ip.validate(None, "999.0.0.1")
    ip_messages = " ".join(str(err) for err in caught_ip.value.errors)
    assert "maximum length" in ip_messages
    assert "IPv4" in ip_messages
    assert len(caught_ip.value.errors) >= 2


def test_named_identity_facades_collect_all_keeps_extra_errors():
    aadhaar = AadhaarCardValidator(min_length=20, collect_all=True, debug=True)
    with pytest.raises(ValidationErrors) as caught_a:
        aadhaar.validate(None, "1234")
    a_messages = " ".join(str(err) for err in caught_a.value.errors)
    assert "minimum length" in a_messages
    assert "Aadhaar" in a_messages

    pan = PANCardValidator(min_length=20, collect_all=True, debug=True)
    with pytest.raises(ValidationErrors) as caught_p:
        pan.validate(None, "AA")
    p_messages = " ".join(str(err) for err in caught_p.value.errors)
    assert "minimum length" in p_messages
    assert "PAN" in p_messages

    expiry = ExpiryValidator(
        expire_after="2020-01-01", min_length=20, collect_all=True, debug=True
    )
    with pytest.raises(ValidationErrors) as caught_e:
        expiry.validate(None, "short")
    e_messages = " ".join(str(err) for err in caught_e.value.errors)
    assert "minimum length" in e_messages
    assert "expired" in e_messages


def test_named_facade_fail_fast_still_stops_before_extra():
    card = PaymentCardValidator(min_length=20, debug=True)
    with pytest.raises(ValueError, match="minimum length") as caught:
        card.validate(None, "4111")
    assert not isinstance(caught.value, ValidationErrors)
    assert "payment card" not in str(caught.value)


def test_named_extra_only_collect_all_is_validation_errors():
    card = PaymentCardValidator(collect_all=True, debug=True)
    with pytest.raises(ValidationErrors) as caught:
        card.validate(None, "0000000000000000")
    assert any("payment card" in str(err) for err in caught.value.errors)


def test_date_and_path_named_extras_join_collect_all():
    field = DateValidator(
        in_choice=[datetime.date(2020, 1, 1)], collect_all=True, debug=True
    )
    with pytest.raises(ValidationErrors) as caught:
        field.validate(None, datetime.datetime(2020, 1, 1))
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "datetime.date" in messages
    assert "expect values in" in messages
    assert len(caught.value.errors) >= 2

    allowed = pathlib.Path("allowed-ux-valio-path")
    path = PathValidator(path_exists=True, in_choice=[allowed], collect_all=True, debug=True)
    missing = pathlib.Path("no-such-ux-valio-path")
    with pytest.raises(ValidationErrors) as caught_p:
        path.validate(None, missing)
    p_messages = " ".join(str(err) for err in caught_p.value.errors)
    assert "expect values in" in p_messages
    assert "existing path" in p_messages
