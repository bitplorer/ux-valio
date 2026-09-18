# SPDX-License-Identifier: MIT
"""PANCardValidator: identity fullmatch ∩ Luhn mod 26. Not findall + unused verify."""

from dataclasses import dataclass

import pytest

from ux_valio import PANCardValidator

# Format [A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z] and Luhn mod 26 (A=0 … Z=25).
VALID_PAN = "AAAPA1111F"
# Same 10-char shape; check letter fails Luhn mod 26.
FORMAT_ONLY_PAN = "AAAPA1111G"


@pytest.fixture
def Card():
    @dataclass
    class Card:
        pan: str = PANCardValidator(debug=True, logger=False)

    return Card


def test_format_and_checksum_valid_pan_is_accepted(Card):
    assert Card(pan=VALID_PAN).pan == VALID_PAN


def test_format_valid_checksum_invalid_pan_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(pan=FORMAT_ONLY_PAN)


def test_substring_pan_is_rejected(Card):
    with pytest.raises(ValueError):
        Card(pan=f"xx{VALID_PAN}yy")


def test_lowercase_pan_is_stored_uppercase(Card):
    assert Card(pan=VALID_PAN.lower()).pan == VALID_PAN


def test_grouped_pan_is_stored_compact(Card):
    assert Card(pan="AAAPA 1111 F").pan == VALID_PAN


def test_wrong_holder_type_is_rejected(Card):
    # Fourth character D is not in ABCFGHLJPTK.
    with pytest.raises(ValueError):
        Card(pan="AAADA1111F")
