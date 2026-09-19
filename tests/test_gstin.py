# SPDX-License-Identifier: MIT
"""GSTINValidator: 15-char format ∩ Luhn mod 36. Not a GST portal lookup."""

from dataclasses import dataclass

import pytest

from ux_valio import GSTINValidator

VALID_GSTIN = "09AAAPA1111F1ZP"
KNOWN_GSTIN = "27AAPFU0939F1ZV"
FORMAT_ONLY = "27AAPFU0939F1ZA"


@pytest.fixture
def Firm():
    @dataclass
    class Firm:
        gstin: str = GSTINValidator()

    return Firm


def test_checksum_valid_gstin_is_accepted(Firm):
    assert Firm(gstin=VALID_GSTIN).gstin == VALID_GSTIN
    assert Firm(gstin=KNOWN_GSTIN).gstin == KNOWN_GSTIN


def test_format_valid_checksum_invalid_gstin_is_rejected(Firm):
    with pytest.raises(ValueError):
        Firm(gstin=FORMAT_ONLY)


def test_lowercase_gstin_is_stored_uppercase(Firm):
    assert Firm(gstin=VALID_GSTIN.lower()).gstin == VALID_GSTIN


def test_grouped_gstin_is_stored_compact(Firm):
    assert Firm(gstin="09 AAAPA1111F 1Z P").gstin == VALID_GSTIN


def test_bad_state_code_is_rejected(Firm):
    with pytest.raises(ValueError):
        Firm(gstin="00AAAPA1111F1ZP")
    with pytest.raises(ValueError):
        Firm(gstin="39AAAPA1111F1ZP")


def test_other_territory_and_centre_gstin_are_accepted(Firm):
    assert Firm(gstin="97AAAPA1111F1ZK").gstin == "97AAAPA1111F1ZK"
    assert Firm(gstin="99AAAPA1111F1ZG").gstin == "99AAAPA1111F1ZG"


def test_substring_gstin_is_rejected(Firm):
    with pytest.raises(ValueError):
        Firm(gstin=f"xx{VALID_GSTIN}yy")
