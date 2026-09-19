# SPDX-License-Identifier: MIT
"""Address-form identities: US state, Indian state, IBAN registry length."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    IBANValidator,
    IndiaStateCodeValidator,
    USStateValidator,
)


def test_us_state_and_territory():
    @dataclass
    class Addr:
        state: str = USStateValidator()

    assert Addr(state="ca").state == "CA"
    assert Addr(state="PR").state == "PR"
    with pytest.raises(ValueError):
        Addr(state="XX")


def test_india_state_udyam_not_iso_ct():
    @dataclass
    class Addr:
        state: str = IndiaStateCodeValidator()

    assert Addr(state="mh").state == "MH"
    assert Addr(state="CG").state == "CG"
    with pytest.raises(ValueError):
        Addr(state="CT")


def test_iban_rejects_wrong_national_length():
    @dataclass
    class Acct:
        iban: str = IBANValidator()

    assert Acct(iban="GB82 WEST 1234 5698 7654 32").iban == "GB82WEST12345698765432"
    with pytest.raises(ValueError):
        Acct(iban="NO82WEST12345698765432")
