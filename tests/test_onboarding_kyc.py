# SPDX-License-Identifier: MIT
"""Onboarding KYC identities: SSN, EIN, NINO, SIN, Mexican RFC."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    CanadianSINValidator,
    EINValidator,
    MexicoRFCValidator,
    NINOValidator,
    SSNValidator,
)


def test_ssn_and_ein():
    @dataclass
    class Us:
        ssn: str = SSNValidator()
        ein: str = EINValidator()

    row = Us(ssn="856-45-6789", ein="12-3456789")
    assert row.ssn == "856456789"
    assert row.ein == "123456789"
    with pytest.raises(ValueError):
        Us(ssn="000-12-3456", ein="123456789")
    with pytest.raises(ValueError):
        Us(ssn="856456789", ein="00-3456789")


def test_nino_hmrc_prefix():
    @dataclass
    class Uk:
        nino: str = NINOValidator()

    assert Uk(nino="ab 12 34 56 c").nino == "AB123456C"
    with pytest.raises(ValueError):
        Uk(nino="QQ123456A")


def test_sin_luhn():
    @dataclass
    class Ca:
        sin: str = CanadianSINValidator()

    assert Ca(sin="046 454 286").sin == "046454286"
    with pytest.raises(ValueError):
        Ca(sin="000000000")


def test_mexico_rfc_person_and_company():
    @dataclass
    class Mx:
        rfc: str = MexicoRFCValidator()

    assert Mx(rfc="gode561231gr8").rfc == "GODE561231GR8"
    assert Mx(rfc="ABC010101AA3").rfc == "ABC010101AA3"
    with pytest.raises(ValueError):
        Mx(rfc="GODE561231GR9")
