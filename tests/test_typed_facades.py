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
    DateTimeValidator,
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
    URLValidator,
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
    assert Price(n="1.50").n == decimal.Decimal("1.50")
    with pytest.raises(TypeError):
        Price(n=1.5)
    with pytest.raises(ValueError):
        Price(n="not-a-decimal")


def test_coercing_facades_bind_str_or_stored_type():
    """Owner annotation may be T, str, or T | str. Stored value is T."""
    raw = "12345678-1234-5678-1234-567812345678"

    @dataclass
    class AsUuid:
        u: uuid.UUID = UUIDValidator(debug=True)

    @dataclass
    class AsStr:
        u: str = UUIDValidator(debug=True)

    @dataclass
    class AsEither:
        u: uuid.UUID | str = UUIDValidator(debug=True)

    stored = uuid.UUID(raw)
    assert AsUuid(u=raw).u == stored
    assert AsStr(u=raw).u == stored
    assert AsEither(u=raw).u == stored
    assert isinstance(AsStr(u=raw).u, uuid.UUID)

    @dataclass
    class PathAsStr:
        p: str = PathValidator(debug=True)

    path = PathAsStr(p="/tmp/ux-valio-path")
    assert isinstance(path.p, pathlib.Path)
    assert path.p == pathlib.Path("/tmp/ux-valio-path")

    @dataclass
    class DayAsStr:
        d: str = DateValidator(debug=True)

    assert DayAsStr(d="2020-01-02").d == datetime.date(2020, 1, 2)


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


def test_email_validator_accepts_identity_address():
    @dataclass
    class Contact:
        email: str = EmailValidator(debug=True)

    assert Contact(email="user@example.com").email == "user@example.com"
    with pytest.raises(ValueError):
        Contact(email="not-an-email")


def test_email_validator_rejects_substring():
    @dataclass
    class Contact:
        email: str = EmailValidator(debug=True)

    wrapped = "prefix user@example.com suffix"
    with pytest.raises(ValueError):
        Contact(email=wrapped)


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


def test_datetime_validator_parses_iso_and_rejects_plain_date():
    @dataclass
    class When:
        t: datetime.datetime = DateTimeValidator(debug=True)

    moment = datetime.datetime(2020, 1, 2, 12, 30)
    assert When(t=moment).t == moment
    assert When(t="2020-01-02T12:30:00").t == moment
    assert When(t="2020-01-02 12:30:00").t == moment
    with pytest.raises(TypeError):
        When(t=datetime.date(2020, 1, 2))
    with pytest.raises(ValueError, match="ISO datetime"):
        When(t="not-a-datetime")
    with pytest.raises(ValueError, match="ISO datetime"):
        When(t="02-01-2020")


def test_datetime_post_validate_cannot_store_a_plain_date():
    from ux_valio.validators.hooks import HookHost

    field = DateTimeValidator(debug=True)

    def to_date(instance, value):
        return datetime.date(2020, 1, 2)

    @dataclass
    class When:
        t: datetime.datetime = field

    field.add_process_post_validate(to_date, namespace=HookHost._owner_key(When))
    with pytest.raises(TypeError):
        When(t="2020-01-02T12:00:00")


def test_uuid_post_validate_cannot_store_a_str():
    from ux_valio.validators.hooks import HookHost

    field = UUIDValidator(debug=True)
    raw = "12345678-1234-5678-1234-567812345678"

    def smash(instance, value):
        return raw

    @dataclass
    class Row:
        u: uuid.UUID = field

    field.add_process_post_validate(smash, namespace=HookHost._owner_key(Row))
    with pytest.raises(TypeError):
        Row(u=raw)


def test_url_validator_requires_scheme_and_netloc():
    @dataclass
    class Link:
        href: str = URLValidator(debug=True)

    assert Link(href="https://example.com/path?q=1").href == "https://example.com/path?q=1"
    assert Link(href="http://localhost:8080").href == "http://localhost:8080"
    assert Link(href="http://[::1]/").href == "http://[::1]/"
    with pytest.raises(ValueError, match="URL"):
        Link(href="example.com")
    with pytest.raises(ValueError, match="URL"):
        Link(href="/relative/path")
    with pytest.raises(ValueError, match="URL"):
        Link(href="not a url")


def test_url_post_validate_cannot_store_a_lie():
    from ux_valio.validators.hooks import HookHost

    field = URLValidator(debug=True)

    def smash(instance, value):
        return "not-a-url"

    @dataclass
    class Link:
        href: str = field

    field.add_process_post_validate(smash, namespace=HookHost._owner_key(Link))
    with pytest.raises(ValueError, match="URL"):
        Link(href="https://example.com")
