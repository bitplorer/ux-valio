# SPDX-License-Identifier: MIT
"""IMEIValidator: 15-digit identity ∩ Luhn."""

from dataclasses import dataclass

import pytest

from ux_valio import IMEIValidator

VALID_IMEI = "490154203237518"
FORMAT_ONLY = "490154203237519"


@pytest.fixture
def Handset():
    @dataclass
    class Handset:
        imei: str = IMEIValidator()

    return Handset


def test_luhn_valid_imei_is_accepted(Handset):
    assert Handset(imei=VALID_IMEI).imei == VALID_IMEI


def test_format_valid_checksum_invalid_imei_is_rejected(Handset):
    with pytest.raises(ValueError):
        Handset(imei=FORMAT_ONLY)


def test_grouped_imei_is_stored_compact(Handset):
    assert Handset(imei="49 015420 323751 8").imei == VALID_IMEI


def test_short_imei_is_rejected(Handset):
    with pytest.raises(ValueError):
        Handset(imei="49015420323751")
