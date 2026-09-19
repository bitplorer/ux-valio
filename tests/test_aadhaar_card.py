# SPDX-License-Identifier: MIT
"""AadhaarCardValidator: 12-digit identity ∩ Verhoeff. Not findall substring."""

from dataclasses import dataclass

import pytest

from ux_valio import AadhaarCardValidator

# 12-digit Verhoeff-valid vector (stdlib tables; no network).
VALID_AADHAAR = "234567890124"
INVALID_CHECKSUM = "234567890125"


@pytest.fixture
def Card():
    @dataclass
    class Card:
        aadhaar: str = AadhaarCardValidator(debug=True, logger=False)

    return Card


def test_verhoeff_valid_aadhaar_is_accepted(Card):
    assert Card(aadhaar=VALID_AADHAAR).aadhaar == VALID_AADHAAR


def test_uidai_reserved_first_digit_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(aadhaar="123456789006")


def test_one_digit_mutation_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(aadhaar=INVALID_CHECKSUM)


def test_non_digit_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(aadhaar="23456789012A")


def test_wrong_length_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(aadhaar=VALID_AADHAAR[:-1])
    with pytest.raises(ValueError):
        Card(aadhaar=VALID_AADHAAR + "0")
    with pytest.raises(ValueError):
        Card(aadhaar="")


def test_substring_containing_valid_aadhaar_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(aadhaar=f"prefix {VALID_AADHAAR} suffix")


def test_uidai_grouped_aadhaar_is_stored_compact(Card):
    assert Card(aadhaar="2345 6789 0124").aadhaar == VALID_AADHAAR
    assert Card(aadhaar="2345-6789-0124").aadhaar == VALID_AADHAAR
    assert Card(aadhaar=f"  {VALID_AADHAAR}  ").aadhaar == VALID_AADHAAR
