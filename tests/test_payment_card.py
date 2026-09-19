# SPDX-License-Identifier: MIT
"""PaymentCardValidator: brand ∩ Luhn. A Luhn-valid generator must not pass."""

from dataclasses import dataclass

import pytest

from ux_valio import PaymentCardValidator


@pytest.fixture
def Card():
    @dataclass
    class Card:
        c: str = PaymentCardValidator(debug=True, logger=False)

    return Card


def test_visa_test_number_is_accepted(Card):
    assert Card(c="4111111111111111").c == "4111111111111111"


def test_printed_visa_grouping_is_stored_compact(Card):
    assert Card(c="4111 1111 1111 1111").c == "4111111111111111"
    assert Card(c="4111-1111-1111-1111").c == "4111111111111111"


def test_luhn_valid_non_brand_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(c="0000000000000000")
    with pytest.raises(ValueError):
        Card(c="79927398713")


def test_luhn_invalid_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(c="4111111111111112")


def test_mastercard_2_series_is_accepted(Card):
    assert Card(c="2221000000000009").c == "2221000000000009"


def test_amex_discover_rupay_brand_numbers_are_accepted(Card):
    assert Card(c="378282246310005").c == "378282246310005"
    assert Card(c="6011111111111117").c == "6011111111111117"
    assert Card(c="6000000000000007").c == "6000000000000007"


def test_rupay_does_not_claim_dead_6521_branch():
    from ux_valio.facades.named.finance import _RUPAY
    assert "52[12]" not in _RUPAY.pattern
    assert _RUPAY.fullmatch("6521000000000000") is None
    assert _RUPAY.fullmatch("6000000000000000") is not None
