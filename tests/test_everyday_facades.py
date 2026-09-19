# SPDX-License-Identifier: MIT
"""Everyday address / rail / portal identities every app reimplements."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    CAPostalCodeValidator,
    CLABEValidator,
    CUSIPValidator,
    ISSNValidator,
    LocaleValidator,
    SemVerValidator,
    UKPostcodeValidator,
    UKSortCodeValidator,
    USZipCodeValidator,
)


def test_us_zip_five_and_plus4():
    @dataclass
    class Addr:
        zip: str = USZipCodeValidator()

    assert Addr(zip="90210").zip == "90210"
    assert Addr(zip="90210-1234").zip == "902101234"
    with pytest.raises(ValueError):
        Addr(zip="9021")


def test_ca_and_uk_postal_normalize():
    @dataclass
    class Addr:
        ca: str = CAPostalCodeValidator()
        uk: str = UKPostcodeValidator()

    row = Addr(ca="k1a0b1", uk="sw1a1aa")
    assert row.ca == "K1A 0B1"
    assert row.uk == "SW1A 1AA"


def test_clabe_and_uk_sort():
    @dataclass
    class Payout:
        clabe: str = CLABEValidator()
        sort: str = UKSortCodeValidator()

    assert Payout(clabe="032180000118359719", sort="12-34-56").sort == "123456"
    with pytest.raises(ValueError):
        Payout(clabe="032180000118359710", sort="123456")


def test_cusip_and_issn_checksum():
    @dataclass
    class Listing:
        cusip: str = CUSIPValidator()
        issn: str = ISSNValidator()

    row = Listing(cusip="037833100", issn="0378-5955")
    assert row.cusip == "037833100"
    assert row.issn == "03785955"
    with pytest.raises(ValueError):
        Listing(cusip="037833101", issn="03785955")


def test_locale_and_semver():
    @dataclass
    class Pref:
        locale: str = LocaleValidator()
        version: str = SemVerValidator()

    row = Pref(locale="en_in", version="1.2.3")
    assert row.locale == "en-IN"
    assert row.version == "1.2.3"
    with pytest.raises(ValueError):
        Pref(locale="xx-IN", version="1.2.3")
    with pytest.raises(ValueError):
        Pref(locale="en", version="01.2.3")
