# SPDX-License-Identifier: MIT
"""Measure host setattr vs one-shot native apply of closed plans.

Hot path A: many ``setattr``s on a dataclass ``Box`` field with a closed
``IntegerValidator`` / ``FloatValidator`` bound plan, a closed
``StringValidator`` / ``BytesValidator`` length plan, a closed
``IntegerEnumValidator`` member-set plan, a closed
``StringEnumValidator`` UTF-8 member-set plan, a closed
``BooleanValidator`` exact-bool type door, a closed
``DecimalValidator`` exact-Decimal type door, a closed
``DateValidator`` date type door, a closed
``DateTimeValidator`` datetime type door, a closed
``UUIDValidator`` UUID type door, a closed
``IPv4Validator`` / ``IPv6Validator`` / ``IPAddressValidator``
string-identity door, or a closed ``PathValidator`` Path type door
(taught API, soul stays
Python). Enum, Boolean, Decimal, Date, DateTime, UUID, IP, and Path
path A clear the native plan after bind so the loop is pure Python
setattr. Decimal values are exact ``Decimal`` instances, Date /
DateTime values are exact ``date`` / ``datetime`` instances, UUID
values are exact ``uuid.UUID`` instances, and Path values are exact
``pathlib.Path`` instances (string coerce is host
``_pre_validate``, not this apply-only comparison). IP values
are the given address strings (the facades do not coerce to
``ipaddress`` objects). ``path_exists`` is not in this comparison.

Hot path B: ``compile_integer(...)`` / ``compile_float(...)`` /
``compile_string(...)`` / ``compile_bytes(...)`` /
``compile_integer_enum(...)`` / ``compile_string_enum(...)`` /
``compile_boolean()`` / ``compile_decimal()`` /
``compile_date()`` / ``compile_datetime()`` / ``compile_uuid()`` /
``compile_ip(kind)`` / ``compile_path()`` once, then
``apply_integer`` / ``apply_float`` / ``apply_string`` / ``apply_bytes`` /
``apply_integer_enum`` / ``apply_string_enum`` / ``apply_boolean`` /
``apply_decimal`` / ``apply_date`` / ``apply_datetime`` / ``apply_uuid`` /
``apply_ip`` / ``apply_path`` on the
``ux_valio_native`` peer. That is
plan apply only — not a claim that product setattr is 70× after host
store/raise. Not Cap Door B.

Families: MinValue, MaxValue, GreaterThan, LessThan, Equal, min+max
range — once for Integer, once for Float — plus String and Bytes
MinLength / MaxLength / Length / min+max range, plus one IntegerEnum
member set, one StringEnum UTF-8 member set, one Boolean exact
``bool`` type door (no coerce of ``1`` / ``0``), one Decimal exact
``decimal.Decimal`` type door (no coerce of ``float`` / ``int`` /
``bool``; no scale unit), one Date ``datetime.date`` type door
(``datetime.datetime`` extracts because it subclasses ``date``; raw
``str`` does not coerce), and one DateTime ``datetime.datetime`` type
door (a plain ``date`` does not extract; raw ``str`` does not coerce),
one Uuid ``uuid.UUID`` type door (raw ``str`` / ``int`` / ``bool`` /
``bytes`` do not coerce), one IP string-identity door per
facade (``ipv4`` / ``ipv6`` / ``ip``; the stored value stays the
given string; ``int`` / ``bytes`` are not coerced), and one Path
``pathlib.Path`` type door (raw ``str`` / ``int`` / ``bool`` /
``bytes`` / ``PurePath`` do not coerce; ``path_exists`` stays host).
Switch bar:
FAIL (KEEP Python) unless host ns/op is >= 3× native ns/op. A family
below the bar is not claimed native (KEEP host for that family).

Usage::

    python benches/measure_host_peer.py
    python benches/measure_host_peer.py --ci
"""

import argparse
import datetime
import decimal
import enum
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NATIVE_DIR = ROOT / "native"
SWITCH_BAR = 3.0
DEFAULT_ITERS = 400_000
DEFAULT_WARMUP = 20_000
PASSING_0_7 = (0, 1, 2, 3, 4, 5, 6, 7)
PASSING_1_8 = (1, 2, 3, 4, 5, 6, 7, 8)
PASSING_EQ = (7, 7, 7, 7, 7, 7, 7, 7)
PASSING_0_7_F = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)
PASSING_1_8_F = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0)
PASSING_EQ_F = (7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0)
PASSING_A_H = ("a", "b", "c", "d", "e", "f", "g", "h")
PASSING_LEN3 = ("abc", "abc", "abc", "abc", "abc", "abc", "abc", "abc")
PASSING_A_H_B = (b"a", b"b", b"c", b"d", b"e", b"f", b"g", b"h")
PASSING_LEN3_B = (b"abc", b"abc", b"abc", b"abc", b"abc", b"abc", b"abc", b"abc")
PASSING_BOOL = (True, False, True, False, True, False, True, False)
PASSING_DECIMAL = (
    decimal.Decimal("1.23"),
    decimal.Decimal("0"),
    decimal.Decimal("2.50"),
    decimal.Decimal("10"),
    decimal.Decimal("0.01"),
    decimal.Decimal("1.23"),
    decimal.Decimal("0"),
    decimal.Decimal("4"),
)
PASSING_DATE = (
    datetime.date(2020, 1, 2),
    datetime.date(2020, 2, 3),
    datetime.date(1999, 12, 31),
    datetime.date(2024, 2, 29),
    datetime.date(2010, 6, 15),
    datetime.date(2020, 1, 2),
    datetime.date(2030, 7, 4),
    datetime.date(1970, 1, 1),
)
PASSING_DATETIME = (
    datetime.datetime(2020, 1, 2, 3, 4, 5),
    datetime.datetime(2020, 1, 2),
    datetime.datetime(1999, 12, 31, 23, 59),
    datetime.datetime(2024, 2, 29, 12, 0),
    datetime.datetime(2010, 6, 15, 8, 30),
    datetime.datetime(2020, 1, 2, 3, 4, 5),
    datetime.datetime(2030, 7, 4, 0, 0, 1),
    datetime.datetime(1970, 1, 1),
)
PASSING_UUID = (
    uuid.UUID("12345678-1234-5678-1234-567812345678"),
    uuid.UUID("00000000-0000-0000-0000-000000000000"),
    uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"),
    uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
    uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8"),
    uuid.UUID("550e8400-e29b-41d4-a716-446655440000"),
    uuid.UUID("01234567-89ab-cdef-0123-456789abcdef"),
    uuid.UUID("12345678-1234-5678-1234-567812345678"),
)
PASSING_IPV4 = (
    "127.0.0.1",
    "0.0.0.0",
    "255.255.255.255",
    "10.0.0.1",
    "192.168.0.1",
    "8.8.8.8",
    "1.2.3.4",
    "127.0.0.1",
)
PASSING_IPV6 = (
    "::1",
    "::",
    "1::",
    "fe80::1%eth0",
    "::ffff:192.0.2.1",
    "2001:db8::1",
    "0:0:0:0:0:0:0:1",
    "2001:DB8::1",
)
PASSING_IP = (
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "2001:db8::",
    "10.1.2.3",
    "fe80::1%1",
    "::ffff:192.0.2.1",
    "8.8.4.4",
)
PASSING_PATH = (
    pathlib.Path("/tmp/ux-valio-a"),
    pathlib.Path("folder/file"),
    pathlib.Path("."),
    pathlib.Path(""),
    pathlib.Path("/var/tmp"),
    pathlib.Path("a"),
    pathlib.Path("/tmp/ux-valio-b"),
    pathlib.Path("rel"),
)


@dataclass(frozen=True)
class PlanFamily:
    name: str
    facade: str
    compile_attr: str
    apply_attr: str
    annotation: type
    field_kwargs: dict[str, Any]
    compile_kwargs: dict[str, Any]
    values: tuple[Any, ...]
    seed: Any
    smoke_ok: Any
    smoke_miss: Any
    smoke_kind: str
    label: str
    smoke_raises: type[BaseException] | None = None


def _integer_enum_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="IntegerEnumValidator",
        compile_attr="compile_integer_enum",
        apply_attr="apply_integer_enum",
        annotation=_MeasureRank,
        **kwargs,
    )


def _string_enum_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="StringEnumValidator",
        compile_attr="compile_string_enum",
        apply_attr="apply_string_enum",
        annotation=_MeasureShade,
        **kwargs,
    )


def _integer_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="IntegerValidator",
        compile_attr="compile_integer",
        apply_attr="apply_integer",
        annotation=int,
        **kwargs,
    )


def _float_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="FloatValidator",
        compile_attr="compile_float",
        apply_attr="apply_float",
        annotation=float,
        **kwargs,
    )


def _string_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="StringValidator",
        compile_attr="compile_string",
        apply_attr="apply_string",
        annotation=str,
        **kwargs,
    )


class _MeasureRank(enum.IntEnum):
    """Member set for the IntegerEnum switch test. Not a taught type."""

    M0 = 0
    M1 = 1
    M2 = 2
    M3 = 3
    M4 = 4
    M5 = 5
    M6 = 6
    M7 = 7


_MEASURE_RANK_VALUES = tuple(_MeasureRank)


class _MeasureShade(enum.Enum):
    """UTF-8 member set for the StringEnum switch test. Not a taught type."""

    M0 = "m0"
    M1 = "m1"
    M2 = "m2"
    M3 = "m3"
    M4 = "m4"
    M5 = "m5"
    M6 = "m6"
    M7 = "m7"


_MEASURE_SHADE_VALUES = tuple(_MeasureShade)


def _date_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="DateValidator",
        compile_attr="compile_date",
        apply_attr="apply_date",
        annotation=datetime.date,
        **kwargs,
    )


def _ipv4_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="IPv4Validator",
        compile_attr="compile_ip",
        apply_attr="apply_ip",
        annotation=str,
        **kwargs,
    )


def _ipv6_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="IPv6Validator",
        compile_attr="compile_ip",
        apply_attr="apply_ip",
        annotation=str,
        **kwargs,
    )


def _ip_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="IPAddressValidator",
        compile_attr="compile_ip",
        apply_attr="apply_ip",
        annotation=str,
        **kwargs,
    )


def _path_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="PathValidator",
        compile_attr="compile_path",
        apply_attr="apply_path",
        annotation=pathlib.Path,
        **kwargs,
    )


def _uuid_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="UUIDValidator",
        compile_attr="compile_uuid",
        apply_attr="apply_uuid",
        annotation=uuid.UUID,
        **kwargs,
    )


def _datetime_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="DateTimeValidator",
        compile_attr="compile_datetime",
        apply_attr="apply_datetime",
        annotation=datetime.datetime,
        **kwargs,
    )


def _decimal_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="DecimalValidator",
        compile_attr="compile_decimal",
        apply_attr="apply_decimal",
        annotation=decimal.Decimal,
        **kwargs,
    )


def _boolean_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="BooleanValidator",
        compile_attr="compile_boolean",
        apply_attr="apply_boolean",
        annotation=bool,
        **kwargs,
    )


def _bytes_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="BytesValidator",
        compile_attr="compile_bytes",
        apply_attr="apply_bytes",
        annotation=bytes,
        **kwargs,
    )


INTEGER_FAMILIES = (
    _integer_family(
        name="Integer.MinValue",
        field_kwargs={"min_value": 0},
        compile_kwargs={"min_value": 0},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=5,
        smoke_miss=-1,
        smoke_kind="MinValue",
        label="Integer + MinValue(0)",
    ),
    _integer_family(
        name="Integer.MaxValue",
        field_kwargs={"max_value": 10},
        compile_kwargs={"max_value": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=10,
        smoke_miss=11,
        smoke_kind="MaxValue",
        label="Integer + MaxValue(10)",
    ),
    _integer_family(
        name="Integer.GreaterThan",
        field_kwargs={"gt": 0},
        compile_kwargs={"gt": 0},
        values=PASSING_1_8,
        seed=1,
        smoke_ok=1,
        smoke_miss=0,
        smoke_kind="GreaterThan",
        label="Integer + GreaterThan(0)",
    ),
    _integer_family(
        name="Integer.LessThan",
        field_kwargs={"lt": 10},
        compile_kwargs={"lt": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=9,
        smoke_miss=10,
        smoke_kind="LessThan",
        label="Integer + LessThan(10)",
    ),
    _integer_family(
        name="Integer.Equal",
        field_kwargs={"eq": 7},
        compile_kwargs={"eq": 7},
        values=PASSING_EQ,
        seed=7,
        smoke_ok=7,
        smoke_miss=8,
        smoke_kind="Equal",
        label="Integer + Equal(7)",
    ),
    _integer_family(
        name="Integer.Range",
        field_kwargs={"min_value": 0, "max_value": 10},
        compile_kwargs={"min_value": 0, "max_value": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=5,
        smoke_miss=-1,
        smoke_kind="MinValue",
        label="Integer + MinValue(0) + MaxValue(10)",
    ),
)

FLOAT_FAMILIES = (
    _float_family(
        name="Float.MinValue",
        field_kwargs={"min_value": 0.0},
        compile_kwargs={"min_value": 0.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=5.0,
        smoke_miss=-1.0,
        smoke_kind="MinValue",
        label="Float + MinValue(0.0)",
    ),
    _float_family(
        name="Float.MaxValue",
        field_kwargs={"max_value": 10.0},
        compile_kwargs={"max_value": 10.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=10.0,
        smoke_miss=11.0,
        smoke_kind="MaxValue",
        label="Float + MaxValue(10.0)",
    ),
    _float_family(
        name="Float.GreaterThan",
        field_kwargs={"gt": 0.0},
        compile_kwargs={"gt": 0.0},
        values=PASSING_1_8_F,
        seed=1.0,
        smoke_ok=1.0,
        smoke_miss=0.0,
        smoke_kind="GreaterThan",
        label="Float + GreaterThan(0.0)",
    ),
    _float_family(
        name="Float.LessThan",
        field_kwargs={"lt": 10.0},
        compile_kwargs={"lt": 10.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=9.0,
        smoke_miss=10.0,
        smoke_kind="LessThan",
        label="Float + LessThan(10.0)",
    ),
    _float_family(
        name="Float.Equal",
        field_kwargs={"eq": 7.0},
        compile_kwargs={"eq": 7.0},
        values=PASSING_EQ_F,
        seed=7.0,
        smoke_ok=7.0,
        smoke_miss=8.0,
        smoke_kind="Equal",
        label="Float + Equal(7.0)",
    ),
    _float_family(
        name="Float.Range",
        field_kwargs={"min_value": 0.0, "max_value": 10.0},
        compile_kwargs={"min_value": 0.0, "max_value": 10.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=5.0,
        smoke_miss=-1.0,
        smoke_kind="MinValue",
        label="Float + MinValue(0.0) + MaxValue(10.0)",
    ),
)

STRING_FAMILIES = (
    _string_family(
        name="String.MinLength",
        field_kwargs={"min_length": 1},
        compile_kwargs={"min_length": 1},
        values=PASSING_A_H,
        seed="a",
        smoke_ok="a",
        smoke_miss="",
        smoke_kind="MinLength",
        label="String + MinLength(1)",
    ),
    _string_family(
        name="String.MaxLength",
        field_kwargs={"max_length": 10},
        compile_kwargs={"max_length": 10},
        values=PASSING_A_H,
        seed="a",
        smoke_ok="a",
        smoke_miss="abcdefghijk",
        smoke_kind="MaxLength",
        label="String + MaxLength(10)",
    ),
    _string_family(
        name="String.Length",
        field_kwargs={"length": 3},
        compile_kwargs={"length": 3},
        values=PASSING_LEN3,
        seed="abc",
        smoke_ok="abc",
        smoke_miss="ab",
        smoke_kind="Length",
        label="String + Length(3)",
    ),
    _string_family(
        name="String.Range",
        field_kwargs={"min_length": 1, "max_length": 10},
        compile_kwargs={"min_length": 1, "max_length": 10},
        values=PASSING_A_H,
        seed="a",
        smoke_ok="a",
        smoke_miss="",
        smoke_kind="MinLength",
        label="String + MinLength(1) + MaxLength(10)",
    ),
)

BYTES_FAMILIES = (
    _bytes_family(
        name="Bytes.MinLength",
        field_kwargs={"min_length": 1},
        compile_kwargs={"min_length": 1},
        values=PASSING_A_H_B,
        seed=b"a",
        smoke_ok=b"a",
        smoke_miss=b"",
        smoke_kind="MinLength",
        label="Bytes + MinLength(1)",
    ),
    _bytes_family(
        name="Bytes.MaxLength",
        field_kwargs={"max_length": 10},
        compile_kwargs={"max_length": 10},
        values=PASSING_A_H_B,
        seed=b"a",
        smoke_ok=b"a",
        smoke_miss=b"abcdefghijk",
        smoke_kind="MaxLength",
        label="Bytes + MaxLength(10)",
    ),
    _bytes_family(
        name="Bytes.Length",
        field_kwargs={"length": 3},
        compile_kwargs={"length": 3},
        values=PASSING_LEN3_B,
        seed=b"abc",
        smoke_ok=b"abc",
        smoke_miss=b"ab",
        smoke_kind="Length",
        label="Bytes + Length(3)",
    ),
    _bytes_family(
        name="Bytes.Range",
        field_kwargs={"min_length": 1, "max_length": 10},
        compile_kwargs={"min_length": 1, "max_length": 10},
        values=PASSING_A_H_B,
        seed=b"a",
        smoke_ok=b"a",
        smoke_miss=b"",
        smoke_kind="MinLength",
        label="Bytes + MinLength(1) + MaxLength(10)",
    ),
)

INTEGER_ENUM_FAMILIES = (
    _integer_enum_family(
        name="IntegerEnum.Member",
        field_kwargs={},
        compile_kwargs={"members": [member.value for member in _MEASURE_RANK_VALUES]},
        values=_MEASURE_RANK_VALUES,
        seed=_MeasureRank.M0,
        smoke_ok=0,
        smoke_miss=8,
        smoke_kind="NotMember",
        label="IntegerEnum + Member(0..7)",
    ),
)

STRING_ENUM_FAMILIES = (
    _string_enum_family(
        name="StringEnum.Member",
        field_kwargs={},
        compile_kwargs={"members": [member.value for member in _MEASURE_SHADE_VALUES]},
        values=_MEASURE_SHADE_VALUES,
        seed=_MeasureShade.M0,
        smoke_ok="m0",
        smoke_miss="m8",
        smoke_kind="NotMember",
        label="StringEnum + Member(m0..m7)",
    ),
)

BOOLEAN_FAMILIES = (
    _boolean_family(
        name="Boolean.Type",
        field_kwargs={},
        compile_kwargs={},
        values=PASSING_BOOL,
        seed=False,
        smoke_ok=True,
        smoke_miss=1,
        smoke_kind="Extract",
        label="Boolean exact bool",
        smoke_raises=TypeError,
    ),
)

DECIMAL_FAMILIES = (
    _decimal_family(
        name="Decimal.Type",
        field_kwargs={},
        compile_kwargs={},
        values=PASSING_DECIMAL,
        seed=decimal.Decimal("0"),
        smoke_ok=decimal.Decimal("1.23"),
        smoke_miss=1.23,
        smoke_kind="Extract",
        label="Decimal exact Decimal",
        smoke_raises=TypeError,
    ),
)

DATE_FAMILIES = (
    _date_family(
        name="Date.Type",
        field_kwargs={},
        compile_kwargs={},
        values=PASSING_DATE,
        seed=datetime.date(2020, 1, 2),
        smoke_ok=datetime.date(2020, 1, 2),
        smoke_miss="2020-01-02",
        smoke_kind="Extract",
        label="Date datetime.date",
        smoke_raises=TypeError,
    ),
)

DATETIME_FAMILIES = (
    _datetime_family(
        name="DateTime.Type",
        field_kwargs={},
        compile_kwargs={},
        values=PASSING_DATETIME,
        seed=datetime.datetime(2020, 1, 2, 3, 4, 5),
        smoke_ok=datetime.datetime(2020, 1, 2, 3, 4, 5),
        smoke_miss=datetime.date(2020, 1, 2),
        smoke_kind="Extract",
        label="DateTime datetime.datetime",
        smoke_raises=TypeError,
    ),
)

UUID_FAMILIES = (
    _uuid_family(
        name="Uuid.Type",
        field_kwargs={},
        compile_kwargs={},
        values=PASSING_UUID,
        seed=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        smoke_ok=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        smoke_miss="12345678-1234-5678-1234-567812345678",
        smoke_kind="Extract",
        label="Uuid uuid.UUID",
        smoke_raises=TypeError,
    ),
)

IP_FAMILIES = (
    _ipv4_family(
        name="IPv4.Identity",
        field_kwargs={},
        compile_kwargs={"kind": "ipv4"},
        values=PASSING_IPV4,
        seed="127.0.0.1",
        smoke_ok="127.0.0.1",
        smoke_miss="::1",
        smoke_kind="NotIp",
        label="IPv4 string identity",
    ),
    _ipv6_family(
        name="IPv6.Identity",
        field_kwargs={},
        compile_kwargs={"kind": "ipv6"},
        values=PASSING_IPV6,
        seed="::1",
        smoke_ok="::1",
        smoke_miss="127.0.0.1",
        smoke_kind="NotIp",
        label="IPv6 string identity",
    ),
    _ip_family(
        name="IP.Identity",
        field_kwargs={},
        compile_kwargs={"kind": "ip"},
        values=PASSING_IP,
        seed="127.0.0.1",
        smoke_ok="::1",
        smoke_miss="not-an-ip",
        smoke_kind="NotIp",
        label="IP string identity",
    ),
)

PATH_FAMILIES = (
    _path_family(
        name="Path.Type",
        field_kwargs={},
        compile_kwargs={},
        values=PASSING_PATH,
        seed=pathlib.Path("/tmp/ux-valio-a"),
        smoke_ok=pathlib.Path("/tmp/ux-valio-a"),
        smoke_miss="/tmp/ux-valio-a",
        smoke_kind="Extract",
        label="Path pathlib.Path",
        smoke_raises=TypeError,
    ),
)

FAMILIES = (
    INTEGER_FAMILIES
    + FLOAT_FAMILIES
    + STRING_FAMILIES
    + BYTES_FAMILIES
    + INTEGER_ENUM_FAMILIES
    + STRING_ENUM_FAMILIES
    + BOOLEAN_FAMILIES
    + DECIMAL_FAMILIES
    + DATE_FAMILIES
    + DATETIME_FAMILIES
    + UUID_FAMILIES
    + IP_FAMILIES
    + PATH_FAMILIES
)


def _ensure_tree_on_path() -> None:
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=True,
        **kwargs,
    )


def _python_cmd() -> list[str]:
    return [sys.executable]


def _rustc_version() -> str | None:
    rustc = shutil.which("rustc")
    if rustc is None:
        return None
    proc = _run([rustc, "--version"])
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or proc.stderr.strip() or None


def _import_peer() -> Any | None:
    try:
        import ux_valio_native
    except ImportError:
        return None
    return ux_valio_native


def _build_peer() -> tuple[Any | None, str | None]:
    """Install maturin and build the local cdylib into this interpreter."""
    rustc = shutil.which("rustc")
    cargo = shutil.which("cargo")
    if rustc is None or cargo is None:
        return None, "SKIP: rustc/cargo not on PATH (native extra is local-only)"
    pip = _run(
        [*_python_cmd(), "-m", "pip", "install", "-q", "maturin>=1.7,<2"],
        cwd=str(ROOT),
    )
    if pip.returncode != 0:
        detail = (pip.stderr or pip.stdout).strip().splitlines()
        tail = detail[-1] if detail else "pip install maturin failed"
        return None, f"SKIP: could not install maturin ({tail})"
    env = os.environ.copy()
    env.setdefault("CARGO_TERM_COLOR", "never")
    # ``venv/bin/python script.py`` does not export VIRTUAL_ENV. maturin
    # develop refuses to install without it.
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        env.setdefault("VIRTUAL_ENV", sys.prefix)
    built = _run(
        [
            *_python_cmd(),
            "-m",
            "maturin",
            "develop",
            "--release",
            "--manifest-path",
            str(NATIVE_DIR / "Cargo.toml"),
        ],
        cwd=str(NATIVE_DIR),
        env=env,
    )
    if built.returncode != 0:
        detail = (built.stderr or built.stdout).strip().splitlines()
        tail = detail[-1] if detail else "maturin develop failed"
        return None, f"SKIP: native peer failed to build ({tail})"
    peer = _import_peer()
    if peer is None:
        return None, "SKIP: peer built but import ux_valio_native failed"
    return peer, None


def _load_facades() -> dict[str, Any]:
    _ensure_tree_on_path()
    try:
        from ux_valio import (
            BooleanValidator,
            BytesValidator,
            DateTimeValidator,
            DateValidator,
            DecimalValidator,
            IPAddressValidator,
            IPv4Validator,
            IPv6Validator,
            PathValidator,
            UUIDValidator,
            FloatValidator,
            IntegerEnumValidator,
            IntegerValidator,
            StringEnumValidator,
            StringValidator,
        )
    except ImportError as err:
        raise SystemExit(
            "FAIL: ux-valio is not importable from the tree. "
            f"Install with `{sys.executable} -m pip install -e .` ({err})"
        ) from err
    return {
        "IntegerValidator": IntegerValidator,
        "FloatValidator": FloatValidator,
        "StringValidator": StringValidator,
        "BytesValidator": BytesValidator,
        "IntegerEnumValidator": IntegerEnumValidator,
        "StringEnumValidator": StringEnumValidator,
        "BooleanValidator": BooleanValidator,
        "DecimalValidator": DecimalValidator,
        "DateValidator": DateValidator,
        "DateTimeValidator": DateTimeValidator,
        "UUIDValidator": UUIDValidator,
        "IPv4Validator": IPv4Validator,
        "IPv6Validator": IPv6Validator,
        "IPAddressValidator": IPAddressValidator,
        "PathValidator": PathValidator,
    }


def _make_box(facades: dict[str, Any], family: PlanFamily) -> Any:
    # Owner annotations must be real types: postponed ``int`` TypeErrors at bind.
    # Force stdlib apply on path A so the switch still compares host units vs
    # plan-apply-only (product setattr is host+store+raise, not this bar).
    from ux_valio.validators._native import _clear_native

    facade = facades[family.facade]
    field = facade(**family.field_kwargs)
    if family.facade in (
        "IntegerEnumValidator",
        "StringEnumValidator",
        "BooleanValidator",
        "DecimalValidator",
        "DateValidator",
        "DateTimeValidator",
        "UUIDValidator",
        "IPv4Validator",
        "IPv6Validator",
        "IPAddressValidator",
        "PathValidator",
    ):
        # Bind first (enum plans compile at ``__set_name__``; Boolean,
        # Decimal, Date, DateTime, UUID, IP, and Path may compile at
        # construct), then drop the plan so path A is pure Python setattr.
        namespace = {"__annotations__": {"n": family.annotation}, "n": field}
        if family.annotation is bool:
            box_name = "BoolBox"
        elif family.annotation is decimal.Decimal:
            box_name = "DecimalBox"
        elif family.annotation is datetime.date:
            box_name = "DateBox"
        elif family.annotation is datetime.datetime:
            box_name = "DateTimeBox"
        elif family.annotation is uuid.UUID:
            box_name = "UuidBox"
        elif family.annotation is pathlib.Path:
            box_name = "PathBox"
        elif family.facade in (
            "IPv4Validator",
            "IPv6Validator",
            "IPAddressValidator",
        ):
            box_name = "IpBox"
        else:
            box_name = "EnumBox"
        box_type = dataclass(type(box_name, (), namespace))
        _clear_native(field)
        return box_type(n=family.seed)
    _clear_native(field)
    seed = family.seed
    if family.annotation is bytes:

        @dataclass
        class BytesBox:
            n: bytes = field

        return BytesBox(n=seed)
    if family.annotation is str:

        @dataclass
        class StrBox:
            n: str = field

        return StrBox(n=seed)
    if family.annotation is float:

        @dataclass
        class FloatBox:
            n: float = field

        return FloatBox(n=seed)

    @dataclass
    class IntBox:
        n: int = field

    return IntBox(n=seed)


def _time_loop(n: int, body: Any) -> int:
    start = time.perf_counter_ns()
    body(n)
    return time.perf_counter_ns() - start


def _host_loop(box: Any, values: tuple[Any, ...]) -> Any:
    mask = len(values) - 1
    name = "n"
    set_attr = setattr

    def run(n: int) -> None:
        for i in range(n):
            set_attr(box, name, values[i & mask])

    return run


def _native_loop(apply: Any, plan: Any, values: tuple[Any, ...]) -> Any:
    if values and isinstance(values[0], enum.Enum):
        values = tuple(item.value for item in values)
    mask = len(values) - 1

    def run(n: int) -> None:
        for i in range(n):
            apply(plan, values[i & mask])

    return run


def _fmt_ns(total_ns: int, n: int) -> str:
    per = total_ns / n
    seconds = total_ns / 1_000_000_000
    return f"{seconds:.6f} s   {per:.1f} ns/op"


def _host_units(facades: dict[str, Any], family: PlanFamily) -> list[str]:
    field = facades[family.facade](**family.field_kwargs)
    return [unit.__name__ for unit in field._active_units]


def _smoke_extract_miss(family: PlanFamily, plan: Any, apply_fn: Any) -> str:
    """Exact type door: the miss raises at extract. No coerce."""
    if family.annotation is bool:
        false_ok = apply_fn(plan, False)
        if false_ok is not None:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, False) "
                f"returned {false_ok!r}, expected None"
            )
        try:
            coerced = apply_fn(plan, 0)
        except family.smoke_raises:
            coerced = None
        else:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, 0) "
                f"returned {coerced!r}; int 0 must not coerce to False"
            )
    if family.annotation is decimal.Decimal:
        zero = decimal.Decimal("0")
        zero_ok = apply_fn(plan, zero)
        if zero_ok is not None:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, Decimal('0')) "
                f"returned {zero_ok!r}, expected None"
            )
        for bad in (1.23, 1, True, "1.23"):
            try:
                coerced = apply_fn(plan, bad)
            except family.smoke_raises:
                continue
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {bad!r}) "
                f"returned {coerced!r}; float/int/bool/str must not coerce to Decimal"
            )
    if family.annotation is datetime.date:
        stamped = datetime.datetime(2020, 1, 2, 3, 4)
        stamped_ok = apply_fn(plan, stamped)
        if stamped_ok is not None:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, datetime) "
                f"returned {stamped_ok!r}, expected None (datetime subclasses date)"
            )
        for bad in ("2020-01-02", 1, True):
            try:
                coerced = apply_fn(plan, bad)
            except family.smoke_raises:
                continue
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {bad!r}) "
                f"returned {coerced!r}; str/int/bool must not coerce to date"
            )
    if family.annotation is datetime.datetime:
        for bad in (datetime.date(2020, 1, 2), "2020-01-02T03:04:05", 1, True):
            try:
                coerced = apply_fn(plan, bad)
            except family.smoke_raises:
                continue
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {bad!r}) "
                f"returned {coerced!r}; date/str/int/bool must not coerce to datetime"
            )
    if family.annotation is uuid.UUID:
        nil = uuid.UUID(int=0)
        nil_ok = apply_fn(plan, nil)
        if nil_ok is not None:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, nil UUID) "
                f"returned {nil_ok!r}, expected None"
            )
        for bad in (
            "12345678-1234-5678-1234-567812345678",
            1,
            True,
            b"\x00" * 16,
        ):
            try:
                coerced = apply_fn(plan, bad)
            except family.smoke_raises:
                continue
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {bad!r}) "
                f"returned {coerced!r}; str/int/bool/bytes must not coerce to UUID"
            )
    if family.annotation is pathlib.Path:
        empty = pathlib.Path("")
        empty_ok = apply_fn(plan, empty)
        if empty_ok is not None:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, Path('')) "
                f"returned {empty_ok!r}, expected None"
            )
        for bad in (
            "/tmp/ux-valio-a",
            pathlib.PurePath("/tmp/pure"),
            1,
            True,
            b"/tmp",
        ):
            try:
                coerced = apply_fn(plan, bad)
            except family.smoke_raises:
                continue
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {bad!r}) "
                f"returned {coerced!r}; str/PurePath/int/bool/bytes must not "
                "coerce to Path"
            )
    try:
        raised = apply_fn(plan, family.smoke_miss)
    except family.smoke_raises:
        return (
            f"SMOKE: {family.name}: {family.compile_attr}({family.compile_kwargs}) "
            f"+ {family.apply_attr}({family.smoke_ok!r}) ok; {family.apply_attr}("
            f"{family.smoke_miss!r}) raises {family.smoke_raises.__name__}"
        )
    raise SystemExit(
        f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {family.smoke_miss!r}) "
        f"returned {raised!r}, expected {family.smoke_raises.__name__}"
    )


def _smoke_family(peer: Any, family: PlanFamily) -> str:
    compile_fn = getattr(peer, family.compile_attr)
    apply_fn = getattr(peer, family.apply_attr)
    plan = compile_fn(**family.compile_kwargs)
    ok = apply_fn(plan, family.smoke_ok)
    if family.smoke_raises is not None:
        if ok is not None:
            raise SystemExit(
                f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {family.smoke_ok}) "
                f"returned {ok!r}, expected None"
            )
        return _smoke_extract_miss(family, plan, apply_fn)
    miss = apply_fn(plan, family.smoke_miss)
    kind = getattr(peer.FailKind, family.smoke_kind)
    if ok is not None:
        raise SystemExit(
            f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {family.smoke_ok}) "
            f"returned {ok!r}, expected None"
        )
    if miss != kind:
        raise SystemExit(
            f"SMOKE FAIL {family.name}: {family.apply_attr}(plan, {family.smoke_miss}) "
            f"returned {miss!r}, expected FailKind.{family.smoke_kind}"
        )
    return (
        f"SMOKE: {family.name}: {family.compile_attr}({family.compile_kwargs}) "
        f"+ {family.apply_attr}({family.smoke_ok}) ok; {family.apply_attr}("
        f"{family.smoke_miss}) -> FailKind.{family.smoke_kind}"
    )


def _smoke(peer: Any) -> str:
    lines = [_smoke_family(peer, family) for family in FAMILIES]
    return "\n".join(lines)


def _report_header(skip_reason: str | None) -> None:
    rustc = _rustc_version() or "not found"
    print("ux-valio host/peer switch test")
    print(f"box:      {platform.platform()}")
    print(f"machine:  {platform.machine()}  {platform.processor() or '-'}")
    print(f"python:   {sys.version.split()[0]}  ({sys.executable})")
    print(f"rustc:    {rustc}")
    print(
        "plan:     Integer i64 + Float f64 bound units "
        "(MinValue/MaxValue/GreaterThan/LessThan/Equal/range); "
        "String length units (MinLength/MaxLength/Length/range, codepoints); "
        "Bytes length units (MinLength/MaxLength/Length/range, byte count); "
        "IntegerEnum i64 member set (compile_integer_enum / apply_integer_enum); "
        "StringEnum UTF-8 member set (compile_string_enum / apply_string_enum); "
        "Boolean exact bool (compile_boolean / apply_boolean); "
        "Decimal exact Decimal (compile_decimal / apply_decimal; no float bridge); "
        "Date datetime.date (compile_date / apply_date; str stays host); "
        "DateTime datetime.datetime (compile_datetime / apply_datetime; "
        "plain date misses); "
        "Uuid uuid.UUID (compile_uuid / apply_uuid; str stays host); "
        "IP string identity (compile_ip / apply_ip; stored str; "
        "NotIp on a bad address); "
        "Path pathlib.Path (compile_path / apply_path; str stays host; "
        "path_exists stays host)"
    )
    print(f"bar:      FAIL unless host ns/op >= {SWITCH_BAR:.1f}× native ns/op")
    print("scope:    not Cap Door B; B is plan-apply-only (not 70× product setattr)")
    if skip_reason:
        print(skip_reason)


def _measure_family(
    iters: int,
    warmup: int,
    peer: Any,
    facades: dict[str, Any],
    family: PlanFamily,
) -> tuple[bool, float, float, float]:
    units = _host_units(facades, family)
    box = _make_box(facades, family)
    host_body = _host_loop(box, family.values)
    compile_fn = getattr(peer, family.compile_attr)
    apply_fn = getattr(peer, family.apply_attr)
    plan = compile_fn(**family.compile_kwargs)
    native_body = _native_loop(apply_fn, plan, family.values)

    host_body(warmup)
    native_body(warmup)

    host_ns = _time_loop(iters, host_body)
    native_ns = _time_loop(iters, native_body)
    host_per = host_ns / iters
    native_per = native_ns / iters
    ratio = host_per / native_per if native_per else float("inf")
    unlocked = ratio >= SWITCH_BAR
    verdict = (
        f"PASS (native extra unlocked): host is {ratio:.2f}× native "
        f"(bar {SWITCH_BAR:.1f}×)"
        if unlocked
        else (
            f"FAIL (KEEP Python): host is {ratio:.2f}× native, "
            f"below the {SWITCH_BAR:.1f}× bar"
        )
    )
    print(f"family:   {family.name}  [{family.label}]")
    print(f"host units: {units}")
    print(f"warmup:   {warmup}   iters: {iters}   values: {family.values}")
    print(f"hot path A: setattr Box.n = {family.facade}({family.field_kwargs})")
    print(f"  {_fmt_ns(host_ns, iters)}")
    print(f"hot path B: native {family.apply_attr}(plan, scalar)  [{family.label}]")
    print(f"  {_fmt_ns(native_ns, iters)}")
    print(f"ratio:    host/native = {ratio:.2f}")
    print(f"VERDICT:  {verdict}")
    print()
    return unlocked, ratio, host_per, native_per


def measure(iters: int, warmup: int, peer: Any, facades: dict[str, Any]) -> int:
    results: list[tuple[PlanFamily, bool, float]] = []
    for family in FAMILIES:
        unlocked, ratio, _host_per, _native_per = _measure_family(
            iters, warmup, peer, facades, family
        )
        results.append((family, unlocked, ratio))
    integer = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "IntegerValidator"]
    floating = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "FloatValidator"]
    string = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "StringValidator"]
    blob = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "BytesValidator"]
    enums = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "IntegerEnumValidator"]
    string_enums = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "StringEnumValidator"
    ]
    failed = [family.name for family, unlocked, _ratio in results if not unlocked]
    int_passed = [family.name for family, unlocked, _ratio in integer if unlocked]
    int_new = [name for name in int_passed if name != "Integer.MinValue"]
    float_failed = [family.name for family, unlocked, _ratio in floating if not unlocked]
    float_passed = [family.name for family, unlocked, _ratio in floating if unlocked]
    string_failed = [family.name for family, unlocked, _ratio in string if not unlocked]
    string_passed = [family.name for family, unlocked, _ratio in string if unlocked]
    bytes_failed = [family.name for family, unlocked, _ratio in blob if not unlocked]
    bytes_passed = [family.name for family, unlocked, _ratio in blob if unlocked]
    enum_failed = [family.name for family, unlocked, _ratio in enums if not unlocked]
    enum_passed = [family.name for family, unlocked, _ratio in enums if unlocked]
    string_enum_failed = [family.name for family, unlocked, _ratio in string_enums if not unlocked]
    string_enum_passed = [family.name for family, unlocked, _ratio in string_enums if unlocked]
    boolean = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "BooleanValidator"
    ]
    boolean_failed = [family.name for family, unlocked, _ratio in boolean if not unlocked]
    boolean_passed = [family.name for family, unlocked, _ratio in boolean if unlocked]
    decimal = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "DecimalValidator"
    ]
    decimal_failed = [family.name for family, unlocked, _ratio in decimal if not unlocked]
    decimal_passed = [family.name for family, unlocked, _ratio in decimal if unlocked]
    if any(not unlocked for _family, unlocked, _ratio in integer):
        print(
            f"SUMMARY: FAIL (KEEP Python) Integer families below {SWITCH_BAR:.1f}×: "
            + ", ".join(name for name in failed if name.startswith("Integer."))
        )
        return 1
    if not int_new:
        print(
            "SUMMARY: SKIP honestly — Integer MinValue met the bar but no new "
            "Integer family (MaxValue/GreaterThan/LessThan/Equal/Range) did"
        )
        return 0
    if float_failed:
        print(
            f"SUMMARY: Float KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(float_failed)
            + ". Do not claim native for those families. "
            + (
                f"Float native unlocked: {', '.join(float_passed)}"
                if float_passed
                else "No Float family met the bar."
            )
        )
        return 1
    if string_failed:
        print(
            f"SUMMARY: String KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(string_failed)
            + ". Do not claim native for those families. "
            + (
                f"String native unlocked: {', '.join(string_passed)}"
                if string_passed
                else "No String family met the bar."
            )
        )
        return 1
    if bytes_failed:
        print(
            f"SUMMARY: Bytes KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(bytes_failed)
            + ". Do not claim native for those families. "
            + (
                f"Bytes native unlocked: {', '.join(bytes_passed)}"
                if bytes_passed
                else "No Bytes family met the bar."
            )
        )
        return 1
    if enum_failed or not enum_passed:
        print(
            f"SUMMARY: IntegerEnum KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(enum_failed or ["(no IntegerEnum family)"])
            + ". Do not claim native for IntegerEnum."
        )
        return 1
    if string_enum_failed or not string_enum_passed:
        print(
            f"SUMMARY: StringEnum KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(string_enum_failed or ["(no StringEnum family)"])
            + ". Do not claim native for StringEnum."
        )
        return 1
    if boolean_failed or not boolean_passed:
        print(
            f"SUMMARY: Boolean KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(boolean_failed or ["(no Boolean family)"])
            + ". Do not claim native for Boolean. Exact bool type door stays on the host."
        )
        return 1
    if decimal_failed or not decimal_passed:
        print(
            f"SUMMARY: Decimal KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(decimal_failed or ["(no Decimal family)"])
            + ". Do not claim native for Decimal. Exact Decimal type door stays on the host."
        )
        return 1
    date = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "DateValidator"
    ]
    date_failed = [family.name for family, unlocked, _ratio in date if not unlocked]
    date_passed = [family.name for family, unlocked, _ratio in date if unlocked]
    if date_failed or not date_passed:
        print(
            f"SUMMARY: Date KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(date_failed or ["(no Date family)"])
            + ". Do not claim native for Date. Date type door stays on the host."
        )
        return 1
    clock = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "DateTimeValidator"
    ]
    clock_failed = [family.name for family, unlocked, _ratio in clock if not unlocked]
    clock_passed = [family.name for family, unlocked, _ratio in clock if unlocked]
    if clock_failed or not clock_passed:
        print(
            f"SUMMARY: DateTime KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(clock_failed or ["(no DateTime family)"])
            + ". Do not claim native for DateTime. DateTime type door stays on the host."
        )
        return 1
    uuids = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "UUIDValidator"
    ]
    uuid_failed = [family.name for family, unlocked, _ratio in uuids if not unlocked]
    uuid_passed = [family.name for family, unlocked, _ratio in uuids if unlocked]
    if uuid_failed or not uuid_passed:
        print(
            f"SUMMARY: Uuid KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(uuid_failed or ["(no Uuid family)"])
            + ". Do not claim native for Uuid. Uuid type door stays on the host."
        )
        return 1
    ips = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade in ("IPv4Validator", "IPv6Validator", "IPAddressValidator")
    ]
    ip_failed = [family.name for family, unlocked, _ratio in ips if not unlocked]
    ip_passed = [family.name for family, unlocked, _ratio in ips if unlocked]
    if ip_failed or not ip_passed:
        print(
            f"SUMMARY: IP KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(ip_failed or ["(no IP family)"])
            + ". Do not claim native for IP. IP string identity stays on the host."
        )
        return 1
    paths = [
        (family, unlocked, ratio)
        for family, unlocked, ratio in results
        if family.facade == "PathValidator"
    ]
    path_failed = [family.name for family, unlocked, _ratio in paths if not unlocked]
    path_passed = [family.name for family, unlocked, _ratio in paths if unlocked]
    if path_failed or not path_passed:
        print(
            f"SUMMARY: Path KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(path_failed or ["(no Path family)"])
            + ". Do not claim native for Path. Path type door stays on the host."
        )
        return 1
    print(
        f"SUMMARY: PASS — {', '.join(int_passed + float_passed + string_passed + bytes_passed + enum_passed + string_enum_passed + boolean_passed + decimal_passed + date_passed + clock_passed + uuid_passed + ip_passed + path_passed)} each >= "
        f"{SWITCH_BAR:.1f}× (plan-apply-only; not 70× product setattr). "
        "Date, DateTime, Uuid, and Path type doors, and IP string identity met the bar."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Measure Integer/Float/String/Bytes/IntegerEnum/StringEnum/Boolean/"
            "Decimal/Date/DateTime/Uuid/IP/Path setattr vs native plan apply."
        )
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Never build Rust. Smoke if the peer is already importable; else skip.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not try maturin develop when the peer is missing.",
    )
    parser.add_argument("--iters", type=int, default=DEFAULT_ITERS)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP)
    args = parser.parse_args(argv)

    facades = _load_facades()
    peer = _import_peer()
    skip_reason: str | None = None
    if peer is None and not args.ci and not args.skip_build:
        peer, skip_reason = _build_peer()
    elif peer is None and args.ci:
        skip_reason = (
            "SKIP: native peer not built (CI has no Rust/PyO3 toolchain; "
            "run locally: python benches/measure_host_peer.py)"
        )
    elif peer is None:
        skip_reason = "SKIP: ux_valio_native is not importable and build was skipped"

    _report_header(skip_reason if peer is None else None)
    if peer is None:
        return 0
    print(_smoke(peer))
    if args.ci:
        print("CI: smoke only (full wall-clock measure is local)")
        return 0
    if args.iters < 1:
        raise SystemExit("--iters must be >= 1")
    if args.warmup < 0:
        raise SystemExit("--warmup must be >= 0")
    return measure(args.iters, args.warmup, peer, facades)


if __name__ == "__main__":
    raise SystemExit(main())
