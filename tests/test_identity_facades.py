# SPDX-License-Identifier: MIT
"""New named identity facades: format ∩ checksum where the scheme has one."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    BICValidator,
    CINValidator,
    DINValidator,
    EANValidator,
    FSSAIValidator,
    IndianPassportValidator,
    ISBNValidator,
    ISINValidator,
    LLPINValidator,
    MACAddressValidator,
    TANValidator,
    UdyamValidator,
    VINValidator,
    VoterIdValidator,
)


def test_bic_8_and_11_are_accepted():
    @dataclass
    class Bank:
        bic: str = BICValidator()

    assert Bank(bic="DEUTDEFF").bic == "DEUTDEFF"
    assert Bank(bic="deut deff 500").bic == "DEUTDEFF500"


def test_bic_wrong_length_is_rejected():
    @dataclass
    class Bank:
        bic: str = BICValidator()

    with pytest.raises(ValueError):
        Bank(bic="DEUTDEF")


def test_isin_luhn_valid_is_accepted():
    @dataclass
    class Holding:
        isin: str = ISINValidator()

    assert Holding(isin="US0378331005").isin == "US0378331005"
    assert Holding(isin="us 0378331005").isin == "US0378331005"


def test_isin_format_only_is_rejected():
    @dataclass
    class Holding:
        isin: str = ISINValidator()

    with pytest.raises(ValueError):
        Holding(isin="US0378331006")


def test_isbn_10_and_13_are_accepted():
    @dataclass
    class Book:
        isbn: str = ISBNValidator()

    assert Book(isbn="978-0-306-40615-7").isbn == "9780306406157"
    assert Book(isbn="0-306-40615-2").isbn == "0306406152"


def test_isbn_checksum_invalid_is_rejected():
    @dataclass
    class Book:
        isbn: str = ISBNValidator()

    with pytest.raises(ValueError):
        Book(isbn="9780306406158")
    with pytest.raises(ValueError):
        Book(isbn="0306406153")


def test_ean_gs1_check_is_required():
    @dataclass
    class Sku:
        ean: str = EANValidator()

    assert Sku(ean="4006381333931").ean == "4006381333931"
    with pytest.raises(ValueError):
        Sku(ean="4006381333932")


def test_vin_iso3779_check_is_required():
    @dataclass
    class Vehicle:
        vin: str = VINValidator()

    assert Vehicle(vin="1HGCM82633A004352").vin == "1HGCM82633A004352"
    assert Vehicle(vin="1M8GDM9AXKP042788").vin == "1M8GDM9AXKP042788"
    with pytest.raises(ValueError):
        Vehicle(vin="1HGCM82634A004352")


def test_vin_forbidden_letters_rejected():
    @dataclass
    class Vehicle:
        vin: str = VINValidator()

    with pytest.raises(ValueError):
        Vehicle(vin="1HGCM82633A00435I")


def test_mac_compact_uppercase_store():
    @dataclass
    class Nic:
        mac: str = MACAddressValidator()

    assert Nic(mac="aa:bb:cc:dd:ee:ff").mac == "AABBCCDDEEFF"
    assert Nic(mac="AA-BB-CC-DD-EE-FF").mac == "AABBCCDDEEFF"
    assert Nic(mac="aabb.ccdd.eeff").mac == "AABBCCDDEEFF"
    with pytest.raises(ValueError):
        Nic(mac="aa:bb:cc:dd:ee")
    with pytest.raises(ValueError):
        Nic(mac="gg:bb:cc:dd:ee:ff")


def test_tan_format_identity():
    @dataclass
    class Deductor:
        tan: str = TANValidator()

    assert Deductor(tan="dela12345a").tan == "DELA12345A"
    with pytest.raises(ValueError):
        Deductor(tan="DELX12345A")


def test_cin_format_identity():
    @dataclass
    class Company:
        cin: str = CINValidator()

    assert Company(cin="u12345mh2000ptc123456").cin == "U12345MH2000PTC123456"
    with pytest.raises(ValueError):
        Company(cin="X12345MH2000PTC123456")


def test_voter_id_epic_format():
    @dataclass
    class Citizen:
        epic: str = VoterIdValidator()

    assert Citizen(epic="abc1234567").epic == "ABC1234567"
    with pytest.raises(ValueError):
        Citizen(epic="AB1234567")


def test_udyam_format_identity():
    @dataclass
    class Firm:
        udyam: str = UdyamValidator()

    assert Firm(udyam="udyam-mh-00-0000001").udyam == "UDYAM-MH-00-0000001"
    with pytest.raises(ValueError):
        Firm(udyam="UDYAM-MH-0000001")


def test_din_eight_digits_keeps_leading_zeros():
    @dataclass
    class Director:
        din: str = DINValidator()

    assert Director(din="00123456").din == "00123456"
    with pytest.raises(ValueError):
        Director(din="1234567")


def test_llpin_strips_hyphen():
    @dataclass
    class Llp:
        llpin: str = LLPINValidator()

    assert Llp(llpin="aab-1234").llpin == "AAB1234"
    with pytest.raises(ValueError):
        Llp(llpin="AA1234")


def test_fssai_licence_and_central_code():
    @dataclass
    class Fbo:
        fssai: str = FSSAIValidator()

    assert Fbo(fssai="10012345678901").fssai == "10012345678901"
    with pytest.raises(ValueError):
        Fbo(fssai="30012345678901")


def test_indian_passport_letter_plus_seven():
    @dataclass
    class Traveller:
        passport: str = IndianPassportValidator()

    assert Traveller(passport="a1234567").passport == "A1234567"
    with pytest.raises(ValueError):
        Traveller(passport="1234567")
