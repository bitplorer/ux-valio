# SPDX-License-Identifier: MIT
"""Typed Door A facades. AttributeValidator stays absent."""

import datetime
import decimal
import enum
import pathlib
import uuid
from dataclasses import dataclass

import pytest

import ux_valio
from ux_valio import (
    BytesValidator,
    DateValidator,
    DecimalValidator,
    EmailValidator,
    EnumValidator,
    FloatValidator,
    IPAddressValidator,
    IPv4Validator,
    IPv6Validator,
    IntegerEnumValidator,
    PathValidator,
    StringEnumValidator,
    UUIDValidator,
)


def test_float_validator_accepts_float_rejects_int_and_str():
    @dataclass
    class Box:
        n: float = FloatValidator(debug=True)

    assert Box(n=1.5).n == 1.5
    with pytest.raises(TypeError):
        Box(n=1)
    with pytest.raises(TypeError):
        Box(n="1.5")


def test_decimal_validator_rejects_float():
    @dataclass
    class Price:
        n: decimal.Decimal = DecimalValidator(debug=True)

    assert Price(n=decimal.Decimal("1.50")).n == decimal.Decimal("1.50")
    with pytest.raises(TypeError):
        Price(n=1.5)


def test_bytes_validator():
    @dataclass
    class Blob:
        b: bytes = BytesValidator(debug=True, min_length=1)

    assert Blob(b=b"ab").b == b"ab"
    with pytest.raises(TypeError):
        Blob(b="ab")
    with pytest.raises(ValueError):
        Blob(b=b"")


def test_date_validator_parses_eu_and_ind_strings():
    @dataclass
    class When:
        d: datetime.date = DateValidator(debug=True)

    assert When(d="2020-01-02").d == datetime.date(2020, 1, 2)
    assert When(d="2020/01/02").d == datetime.date(2020, 1, 2)
    assert When(d="2020:1:2").d == datetime.date(2020, 1, 2)
    assert When(d="02-01-2020").d == datetime.date(2020, 1, 2)
    assert When(d="2/1/2020").d == datetime.date(2020, 1, 2)
    assert When(d="02:01:2020").d == datetime.date(2020, 1, 2)
    # Slash dates are IND day-month-year, not US month-day-year.
    assert When(d="02/01/2020").d == datetime.date(2020, 1, 2)
    with pytest.raises(ValueError):
        When(d="not-a-date")
    with pytest.raises(ValueError):
        When(d="2020-01/02")
    with pytest.raises(ValueError):
        When(d="2020-13-01")
    with pytest.raises(ValueError):
        When(d="29-02-2021")
    with pytest.raises(ValueError):
        When(d="prefix 2020-01-02 suffix")
    with pytest.raises(ValueError):
        When(d="2020-01-02T00:00:00")
    assert When(d=datetime.date(2020, 1, 2)).d == datetime.date(2020, 1, 2)
    assert When(d="29-02-2020").d == datetime.date(2020, 2, 29)
    assert DateValidator().pattern is None


def test_date_validator_rejects_datetime_subclass():
    """datetime.datetime is a date subclass; DateValidator must not store it."""

    @dataclass
    class When:
        d: datetime.date = DateValidator(debug=True)

    moment = datetime.datetime(2020, 1, 1, 12, 0)
    with pytest.raises(TypeError, match="datetime") as caught:
        When(d=moment)
    assert "datetime.date" in str(caught.value)
    day = datetime.date(2020, 1, 1)
    assert When(d=day).d == day


def test_date_validator_still_accepts_plain_date_subclass():
    class Holiday(datetime.date):
        pass

    @dataclass
    class When:
        d: datetime.date = DateValidator(debug=True)

    day = Holiday(2020, 1, 1)
    assert When(d=day).d == day


def test_email_validator_findall():
    @dataclass
    class Contact:
        email: str = EmailValidator(debug=True)

    assert Contact(email="user@example.com").email == "user@example.com"
    with pytest.raises(ValueError):
        Contact(email="not-an-email")


def test_email_validator_findall_is_substring_not_fullmatch():
    @dataclass
    class Contact:
        email: str = EmailValidator(debug=True)

    wrapped = "prefix user@example.com suffix"
    assert Contact(email=wrapped).email == wrapped


def test_uuid_validator_coerces_string():
    raw = "12345678-1234-5678-1234-567812345678"

    @dataclass
    class Row:
        u: uuid.UUID = UUIDValidator(debug=True)

    assert Row(u=raw).u == uuid.UUID(raw)
    assert Row(u=uuid.UUID(raw)).u == uuid.UUID(raw)
    with pytest.raises(ValueError):
        Row(u="not-a-uuid")


def test_path_validator_coerces_str(tmp_path):
    existing = tmp_path / "here"
    existing.mkdir()

    @dataclass
    class Loc:
        p: pathlib.Path = PathValidator(debug=True)

    assert Loc(p=str(existing)).p == existing

    @dataclass
    class MustExist:
        p: pathlib.Path = PathValidator(path_exists=True, debug=True)

    assert MustExist(p=existing).p == existing
    with pytest.raises(FileNotFoundError):
        MustExist(p=tmp_path / "missing")


def test_ip_validators():
    @dataclass
    class V4:
        ip: str = IPv4Validator(debug=True)

    assert V4(ip="127.0.0.1").ip == "127.0.0.1"
    with pytest.raises(ValueError):
        V4(ip="999.0.0.1")

    @dataclass
    class V6:
        ip: str = IPv6Validator(debug=True)

    assert V6(ip="::1").ip == "::1"
    with pytest.raises(ValueError):
        V6(ip="127.0.0.1")

    @dataclass
    class AnyIP:
        ip: str = IPAddressValidator(debug=True)

    assert AnyIP(ip="127.0.0.1").ip == "127.0.0.1"
    assert AnyIP(ip="::1").ip == "::1"
    with pytest.raises(ValueError):
        AnyIP(ip="not-an-ip")


class Color(enum.Enum):
    RED = "red"
    BLUE = "blue"


class Rank(enum.IntEnum):
    LOW = 1
    HIGH = 2


def test_enum_validators():
    @dataclass
    class Flag:
        c: Color = EnumValidator(debug=True)

    assert Flag(c=Color.RED).c is Color.RED
    with pytest.raises(TypeError):
        Flag(c="red")

    @dataclass
    class Grade:
        r: Rank = IntegerEnumValidator(debug=True)

    assert Grade(r=Rank.LOW).r is Rank.LOW
    with pytest.raises(TypeError):
        Grade(r=Color.RED)

    @dataclass
    class Shade:
        c: Color = StringEnumValidator(debug=True)

    assert Shade(c=Color.BLUE).c is Color.BLUE
    with pytest.raises(TypeError):
        Shade(c=Rank.LOW)


def test_attribute_validator_is_not_shipped():
    assert not hasattr(ux_valio, "AttributeValidator")
    assert "AttributeValidator" not in ux_valio.__all__
