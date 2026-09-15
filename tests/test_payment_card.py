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


def test_luhn_valid_non_brand_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(c="0000000000000000")
    with pytest.raises(ValueError):
        Card(c="79927398713")


def test_luhn_invalid_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(c="4111111111111112")
