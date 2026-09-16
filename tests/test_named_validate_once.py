# SPDX-License-Identifier: MIT
"""Named facades must not register themselves on each assign."""

from dataclasses import dataclass

from ux_valio import (
    AadhaarCardValidator,
    DateValidator,
    ExpiryValidator,
    PANCardValidator,
    PaymentCardValidator,
)


def _bags_did_not_grow(validator) -> bool:
    return all(len(fns) <= 1 for fns in validator._custom_validators.values())


def test_payment_card_validator_list_does_not_grow():
    v = PaymentCardValidator(debug=True, logger=False)

    @dataclass
    class Card:
        c: str = v

    Card(c="4111111111111111")
    Card(c="4111111111111111")
    Card(c="4111111111111111")
    assert _bags_did_not_grow(v), v._custom_validators
    assert Card(c="4111111111111111").c == "4111111111111111"


def test_expiry_validator_list_does_not_grow():
    v = ExpiryValidator(expire_before="2020-01-01", debug=True, logger=False)

    @dataclass
    class License:
        key: str = v

    License(key="a")
    License(key="b")
    License(key="c")
    assert _bags_did_not_grow(v), v._custom_validators
    assert License(key="d").key == "d"


def test_aadhaar_card_validator_list_does_not_grow():
    v = AadhaarCardValidator(debug=True, logger=False)

    @dataclass
    class Card:
        a: str = v

    Card(a="234567890124")
    Card(a="234567890124")
    Card(a="234567890124")
    assert _bags_did_not_grow(v), v._custom_validators
    assert Card(a="234567890124").a == "234567890124"


def test_pan_card_validator_list_does_not_grow():
    v = PANCardValidator(debug=True, logger=False)

    @dataclass
    class Card:
        p: str = v

    Card(p="AAAPA1111F")
    Card(p="AAAPA1111F")
    Card(p="AAAPA1111F")
    assert _bags_did_not_grow(v), v._custom_validators
    assert Card(p="AAAPA1111F").p == "AAAPA1111F"


def test_date_validator_list_does_not_grow():
    import datetime

    v = DateValidator(debug=True, logger=False)

    @dataclass
    class When:
        d: datetime.date = v

    day = datetime.date(2020, 1, 1)
    When(d=day)
    When(d=day)
    When(d=day)
    assert _bags_did_not_grow(v), v._custom_validators
    assert When(d=day).d == day
