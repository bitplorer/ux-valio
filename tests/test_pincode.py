# SPDX-License-Identifier: MIT
"""PinCodeValidator: 6-digit India Post identity."""

from dataclasses import dataclass

import pytest

from ux_valio import PinCodeValidator

LUCKNOW = "226001"


@pytest.fixture
def Address():
    @dataclass
    class Address:
        pin: str = PinCodeValidator()

    return Address


def test_valid_pin_is_accepted(Address):
    assert Address(pin=LUCKNOW).pin == LUCKNOW


def test_grouped_pin_is_stored_compact(Address):
    assert Address(pin="226 001").pin == LUCKNOW


def test_leading_zero_pin_is_rejected(Address):
    with pytest.raises(ValueError):
        Address(pin="026001")


def test_five_digit_pin_is_rejected(Address):
    with pytest.raises(ValueError):
        Address(pin="22600")
