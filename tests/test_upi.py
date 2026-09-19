# SPDX-License-Identifier: MIT
"""UPIIdValidator: NPCI VPA identity. Not a PSP lookup."""

from dataclasses import dataclass

import pytest

from ux_valio import UPIIdValidator

VALID_UPI = "ada.kumar@oksbi"


@pytest.fixture
def Wallet():
    @dataclass
    class Wallet:
        vpa: str = UPIIdValidator()

    return Wallet


def test_valid_upi_id_is_accepted(Wallet):
    assert Wallet(vpa=VALID_UPI).vpa == VALID_UPI


def test_uppercase_upi_is_stored_lowercase(Wallet):
    assert Wallet(vpa="Ada.Kumar@OKSBI").vpa == VALID_UPI


def test_phone_local_part_is_accepted(Wallet):
    assert Wallet(vpa="9876543210@ybl").vpa == "9876543210@ybl"


def test_missing_handle_is_rejected(Wallet):
    with pytest.raises(ValueError):
        Wallet(vpa="ada.kumar")


def test_numeric_handle_is_rejected(Wallet):
    with pytest.raises(ValueError):
        Wallet(vpa="ada.kumar@ybl1")
