# SPDX-License-Identifier: MIT
"""E-commerce / SaaS named identity facades."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    ABARoutingValidator,
    CardExpiryValidator,
    CountryCodeValidator,
    CurrencyCodeValidator,
    GTINValidator,
    HSNCodeValidator,
    HostnameValidator,
    LEIValidator,
    SlugValidator,
    TimezoneValidator,
    ULIDValidator,
)


def test_gtin_lengths_and_checksum():
    @dataclass
    class Sku:
        gtin: str = GTINValidator()

    assert Sku(gtin="4006381333931").gtin == "4006381333931"
    assert Sku(gtin="036000291452").gtin == "036000291452"
    assert Sku(gtin="73513537").gtin == "73513537"
    with pytest.raises(ValueError):
        Sku(gtin="4006381333932")


def test_hostname_lowercases_and_rejects_url_and_ipv4():
    @dataclass
    class Tenant:
        host: str = HostnameValidator()

    assert Tenant(host="API.Example.COM.").host == "api.example.com"
    with pytest.raises(ValueError):
        Tenant(host="https://example.com")
    with pytest.raises(ValueError):
        Tenant(host="127.0.0.1")


def test_slug_lowercases_rejects_spaces():
    @dataclass
    class Page:
        slug: str = SlugValidator()

    assert Page(slug="Hello-World").slug == "hello-world"
    with pytest.raises(ValueError):
        Page(slug="Hello World")


def test_currency_and_country_fold_and_reject_unknown():
    @dataclass
    class Price:
        currency: str = CurrencyCodeValidator()
        country: str = CountryCodeValidator()

    row = Price(currency="inr", country="in")
    assert row.currency == "INR"
    assert row.country == "IN"
    with pytest.raises(ValueError):
        Price(currency="INR", country="XX")
    with pytest.raises(ValueError):
        Price(currency="ZZZ", country="IN")


def test_timezone_iana_membership():
    @dataclass
    class Pref:
        tz: str = TimezoneValidator()

    assert Pref(tz="Asia/Kolkata").tz == "Asia/Kolkata"
    assert Pref(tz="UTC").tz == "UTC"
    with pytest.raises(ValueError):
        Pref(tz="Not/AZone")


def test_lei_mod97():
    @dataclass
    class Entity:
        lei: str = LEIValidator()

    assert Entity(lei="5493001KJTIIGC8Y1R12").lei == "5493001KJTIIGC8Y1R12"
    with pytest.raises(ValueError):
        Entity(lei="5493001KJTIIGC8Y1R13")


def test_ulid_crockford():
    @dataclass
    class Row:
        public_id: str = ULIDValidator()

    assert Row(public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV").public_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    with pytest.raises(ValueError):
        Row(public_id="I1ARZ3NDEKTSV4RRFFQ69G5FAV")


def test_card_expiry_mmyy():
    @dataclass
    class Card:
        exp: str = CardExpiryValidator()

    assert Card(exp="12/25").exp == "1225"
    assert Card(exp="12-25").exp == "1225"
    with pytest.raises(ValueError):
        Card(exp="13/25")


def test_hsn_4_6_8():
    @dataclass
    class Line:
        hsn: str = HSNCodeValidator()

    assert Line(hsn="8703").hsn == "8703"
    assert Line(hsn="87032110").hsn == "87032110"
    with pytest.raises(ValueError):
        Line(hsn="870")


def test_aba_checksum():
    @dataclass
    class Payout:
        routing: str = ABARoutingValidator()

    assert Payout(routing="021000021").routing == "021000021"
    with pytest.raises(ValueError):
        Payout(routing="021000022")
