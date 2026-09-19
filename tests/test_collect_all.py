# SPDX-License-Identifier: MIT
"""collect_all omitted is True (continue remaining concerns).

collect_all is not debug-swallow: debug still chooses raise vs append.
``collect_all=False`` is fail-fast. A single collected failure re-raises
as itself; two or more become ValidationErrors.
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
    PhoneNumberValidator,
    RequiredValidator,
    ValidationErrors,
    Validator,
)


def test_collect_all_and_debug_omitted_are_true():
    field = IntegerValidator(min_value=0, multiple_of=2)
    assert field.collect_all is True
    assert field.debug is True

    @dataclass
    class Count:
        n: int = field

    with pytest.raises(ValidationErrors) as caught:
        Count(n=-1)
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "multiple of" in messages
    assert "minimum value" in messages


def test_collect_all_false_is_fail_fast():
    field = IntegerValidator(min_value=0, multiple_of=2, collect_all=False)
    assert field.collect_all is False

    @dataclass
    class Count:
        n: int = field

    with pytest.raises(ValueError, match="multiple of") as caught:
        Count(n=-1)
    assert not isinstance(caught.value, ValidationErrors)


def test_debug_false_still_collects_then_swallows():
    field = IntegerValidator(min_value=0, multiple_of=2, debug=False)
    assert field.collect_all is True
    assert field.debug is False

    @dataclass
    class Count:
        n: int = field

    assert Count(n=-1).n is None
    assert len(field.errors) >= 2
    assert all(not isinstance(err, ValidationErrors) for err in field.errors)


def test_collect_all_debug_true_raises_validation_errors():
    field = IntegerValidator(min_value=0, multiple_of=2)

    @dataclass
    class Count:
        n: int = field

    with pytest.raises(ValidationErrors) as caught:
        Count(n=-1)
    assert len(caught.value.errors) >= 2
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "multiple of" in messages
    assert "minimum value" in messages


def test_collect_all_allof_continues_members():
    field = AllOf(
        MinLengthValidator(min_length=10),
        PatternValidator(pattern=r"xyz"),
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
    )

    @dataclass
    class Pet:
        value: str = field

    with pytest.raises(ValidationErrors) as caught:
        Pet(value="bird")
    assert len(caught.value.errors) >= 2


def test_anyof_collect_all_false_is_one_value_error():
    field = PatternValidator(pattern=r"cat", collect_all=False) | PatternValidator(
        pattern=r"dog", collect_all=False
    )

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
    )
    field = inner & RequiredValidator(required=True)
    assert field.collect_all is True
    assert len(field.validators) == 3


def test_debug_false_does_not_turn_collect_all_off():
    field = Validator(debug=False)
    assert field.collect_all is True
    assert field.debug is False


def test_named_facade_collect_all_keeps_inherited_and_extra_errors():
    """Extra checks after the inherited path must join the collect_all bag."""
    card = PaymentCardValidator(min_length=20)
    with pytest.raises(ValidationErrors) as caught:
        card.validate(None, "4111")
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "minimum length" in messages
    assert "payment card" in messages
    assert len(caught.value.errors) >= 2

    ip = IPv4Validator(max_length=3)
    with pytest.raises(ValidationErrors) as caught_ip:
        ip.validate(None, "999.0.0.1")
    ip_messages = " ".join(str(err) for err in caught_ip.value.errors)
    assert "maximum length" in ip_messages
    assert "IPv4" in ip_messages
    assert len(caught_ip.value.errors) >= 2


def test_named_identity_facades_collect_all_keeps_extra_errors():
    aadhaar = AadhaarCardValidator(min_length=20)
    with pytest.raises(ValidationErrors) as caught_a:
        aadhaar.validate(None, "1234")
    a_messages = " ".join(str(err) for err in caught_a.value.errors)
    assert "minimum length" in a_messages
    assert "Aadhaar" in a_messages

    pan = PANCardValidator(min_length=20)
    with pytest.raises(ValidationErrors) as caught_p:
        pan.validate(None, "AA")
    p_messages = " ".join(str(err) for err in caught_p.value.errors)
    assert "minimum length" in p_messages
    assert "PAN" in p_messages

    expiry = ExpiryValidator(expire_after="2020-01-01", min_length=20)
    with pytest.raises(ValidationErrors) as caught_e:
        expiry.validate(None, "short")
    e_messages = " ".join(str(err) for err in caught_e.value.errors)
    assert "minimum length" in e_messages
    assert "expired" in e_messages


def test_named_facade_fail_fast_still_stops_before_extra():
    card = PaymentCardValidator(min_length=20, collect_all=False)
    with pytest.raises(ValueError, match="minimum length") as caught:
        card.validate(None, "4111")
    assert not isinstance(caught.value, ValidationErrors)
    assert "payment card" not in str(caught.value)


def test_named_extra_only_surfaces():
    card = PaymentCardValidator()
    with pytest.raises(ValueError, match="payment card") as caught:
        card.validate(None, "0000000000000000")
    if isinstance(caught.value, ValidationErrors):
        assert any("payment card" in str(err) for err in caught.value.errors)


def test_date_and_path_named_extras_join_collect_all():
    field = DateValidator(in_choice=[datetime.date(2020, 1, 1)])
    with pytest.raises(ValidationErrors) as caught:
        field.validate(None, datetime.datetime(2020, 1, 1))
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "datetime.date" in messages
    assert "expect values in" in messages
    assert len(caught.value.errors) >= 2

    allowed = pathlib.Path("allowed-ux-valio-path")
    path = PathValidator(path_exists=True, in_choice=[allowed])
    missing = pathlib.Path("no-such-ux-valio-path")
    with pytest.raises(ValidationErrors) as caught_p:
        path.validate(None, missing)
    p_messages = " ".join(str(err) for err in caught_p.value.errors)
    assert "expect values in" in p_messages
    assert "existing path" in p_messages


def test_phone_named_extra_joins_collect_all():
    field = PhoneNumberValidator(region="IN", min_length=20)
    with pytest.raises(ValidationErrors) as caught:
        field.validate(None, "123")
    messages = " ".join(str(err) for err in caught.value.errors)
    assert "minimum length" in messages
    assert "phone number" in messages
    assert len(caught.value.errors) >= 2
