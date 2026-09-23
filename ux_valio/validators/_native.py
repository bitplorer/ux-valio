# SPDX-License-Identifier: MIT
"""Optional native apply (product PyO3 ``ux_valio_native``). Not a taught import.

One module. A private split is worth it only when opening that file
shows one family's walk. Closed detectors, apply, and the bind list
are the same walk for every family, so they stay here. This is not a
``plan`` / ``bound`` / ``length`` mirror of the Rust crate.

``Plan`` is one variant per family. Integer / Float own ``BoundUnit``
values. String / Bytes own ``LengthUnit`` values. IntegerEnum /
StringEnum own a member set. Boolean / Decimal / Date / DateTime /
Uuid are type-door markers. IP owns an address kind (``ipv4`` /
``ipv6`` / ``ip``) and checks a ``str``. There is no shared unit bag.

Bind-time choice: when ``ux_valio_native`` is importable and the
specified path is one closed family, compile that variant once.
Type door is host-first ``isinstance`` then FFI extract (``i64`` /
``f64`` / ``&str`` / ``&[u8]`` / ``bool`` / ``decimal.Decimal`` /
``datetime.date`` / ``datetime.datetime`` / ``uuid.UUID`` / ``str`` for IP);
bound / length / member checks run after extract. StringEnum
extract is the member's ``.value`` as UTF-8 ``&str``. Boolean
extract is exact ``bool`` (``1`` / ``0`` are not coerced). Decimal
extract is exact ``decimal.Decimal`` (``float`` / ``int`` /
``bool`` are not coerced; string coerce stays host
``_pre_validate``). No scale unit. Date extract is
``datetime.date`` (a ``datetime.datetime`` extracts, because it
subclasses ``date``; ``DateValidator`` still rejects it in the
named extra). DateTime extract is ``datetime.datetime`` (a plain
``date`` does not). Uuid extract is ``uuid.UUID`` (a raw ``str``
does not). String coerce for Date, DateTime, and Uuid stays host
``_pre_validate``. IP facades do not coerce: the stored value is
the given string, and ``apply_ip`` mirrors ``ipaddress.IPv4Address``
/ ``IPv6Address`` / ``ip_address`` on that string (``FailKind.NotIp``).
Open TypeValidator / Union / TypedDict /
Annotated / pattern / plain ``EnumValidator`` / Path
stay on the host. A ``BooleanValidator``, ``DecimalValidator``,
``DateValidator``, ``DateTimeValidator``, ``UUIDValidator``,
``IPv4Validator``, ``IPv6Validator``, or ``IPAddressValidator`` with
any extra unit stays on the host. Missing or failed extra → host
``_active_units`` path. No import on the hot path after that
choice. Each family keeps its own ``compile_*`` / ``apply_*`` pair.
Not Cap Door B.
"""

from __future__ import annotations

import datetime
import decimal
import enum
import ipaddress
import types
import uuid
from typing import Any, Union, get_args, get_origin

from ux_valio.errors import raise_collected
from ux_valio.validators.leaves import TypeValidator
from ux_valio.validators.length import LengthValidator
from ux_valio.validators.value import ValueValidator

_native_mod: Any | None = None
_probed = False


def _load_native() -> Any | None:
    """Import the extra once. Failed install is host apply, not a hot-path error."""
    global _native_mod, _probed
    if _probed:
        return _native_mod
    try:
        import ux_valio_native as native
    except ImportError:
        _probed = True
        _native_mod = None
        return None
    except Exception as err:
        raise RuntimeError("ux_valio_native import failed") from err
    _probed = True
    _native_mod = native
    return _native_mod


# Host stores ``eq=`` as ``value``. Compile kwargs are BoundUnit names
# (MinValue / GreaterThan / MaxValue / LessThan / Equal) on
# Plan::Integer and Plan::Float. There is no shared Unit bag.
_HOST_BOUND_TO_COMPILE = (
    ("min_value", "min_value"),
    ("gt", "gt"),
    ("max_value", "max_value"),
    ("lt", "lt"),
    ("value", "eq"),
)

# L1 kwargs stay min_length / max_length / length. Compile kwargs are
# LengthUnit names (MinLength / MaxLength / Length) on Plan::String
# and Plan::Bytes.
_HOST_LENGTH_TO_COMPILE = (
    ("min_length", "min_length"),
    ("max_length", "max_length"),
    ("length", "length"),
)

# Living IP facades store ``str``. The stdlib types are the parsers,
# not the stored type. This module does not import facades; the class
# is the one in ``ux_valio.facades.typed``.
_IP_FACADES = {
    "IPv4Validator": ("ipv4", ipaddress.IPv4Address, "IPv4 address"),
    "IPv6Validator": ("ipv6", ipaddress.IPv6Address, "IPv6 address"),
    "IPAddressValidator": ("ip", ipaddress.ip_address, "IP address"),
}


def _closed_value_bounds(owner: Any, annotation: type, bound_type: type) -> dict[str, Any] | None:
    """Compile kwargs when the specified path is annotation + ValueValidator bounds."""
    if getattr(owner, "annotation", None) is not annotation:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (
        TypeValidator._validate_type,
        ValueValidator._validate_value,
    ):
        return None
    bounds: dict[str, Any] = {}
    for host_name, compile_name in _HOST_BOUND_TO_COMPILE:
        raw = getattr(owner, host_name, None)
        if raw is None:
            continue
        if type(raw) is not bound_type:
            return None
        bounds[compile_name] = raw
    if not bounds:
        return None
    return bounds


def _closed_integer_bounds(owner: Any) -> dict[str, int] | None:
    """Compile kwargs when the specified path is Integer + ValueValidator bounds."""
    return _closed_value_bounds(owner, int, int)


def _closed_float_bounds(owner: Any) -> dict[str, float] | None:
    """Compile kwargs when the specified path is Float + ValueValidator bounds.

    Bounds must be ``float`` (not ``int``). ``FloatValidator(min_value=0)``
    stays on the host, same exact-type lock as Integer rejecting a float
    bound. NaN / ±inf are ``float`` and compile.
    """
    return _closed_value_bounds(owner, float, float)


def _closed_length(owner: Any, annotation: type) -> dict[str, int] | None:
    """Compile kwargs when the specified path is annotation + LengthValidator.

    Bounds must be ``int`` (not ``bool`` / ``float``). Pattern / required /
    value bounds stay on the host.
    """
    if getattr(owner, "annotation", None) is not annotation:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (
        TypeValidator._validate_type,
        LengthValidator._validate_length,
    ):
        return None
    bounds: dict[str, int] = {}
    for host_name, compile_name in _HOST_LENGTH_TO_COMPILE:
        raw = getattr(owner, host_name, None)
        if raw is None:
            continue
        if type(raw) is not int:
            return None
        bounds[compile_name] = raw
    if not bounds:
        return None
    return bounds


def _closed_string_length(owner: Any) -> dict[str, int] | None:
    """Compile kwargs when the specified path is String + LengthValidator.

    Annotation must be ``str``. Bounds must be ``int`` (not ``bool`` /
    ``float``). List / pattern / required stay on the host. Count is
    ``len(str)`` codepoints.
    """
    return _closed_length(owner, str)


def _closed_integer_enum_members(owner: Any) -> list[int] | None:
    """Member ``i64`` values when the path is ``IntegerEnumValidator`` + type.

    Annotation must be a concrete ``enum.IntEnum`` (not ``enum.IntEnum``
    itself, not a union). Every member ``.value`` must be an exact ``int``
    (``bool`` stays on the host). Extra bounds stay on the host. Plain
    ``EnumValidator`` / ``StringEnumValidator`` / ``Validator[SomeIntEnum]``
    stay on the host — this module does not import facades; the facade is
    the class in ``ux_valio.facades.typed``. StringEnum is
    ``_closed_string_enum_members``, not this function.
    """
    if type(owner).__module__ != "ux_valio.facades.typed":
        return None
    if type(owner).__qualname__ != "IntegerEnumValidator":
        return None
    annotation = getattr(owner, "annotation", None)
    if not isinstance(annotation, type) or not issubclass(annotation, enum.IntEnum):
        return None
    if annotation is enum.IntEnum:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    members: list[int] = []
    seen: set[int] = set()
    for member in annotation:
        raw = member.value
        if type(raw) is not int:
            return None
        if raw in seen:
            continue
        seen.add(raw)
        members.append(raw)
    if not members:
        return None
    return members


def _closed_string_enum_members(owner: Any) -> list[str] | None:
    """UTF-8 member values when the path is ``StringEnumValidator`` + type.

    Annotation must be a concrete ``enum.Enum`` (not ``enum.Enum`` itself,
    not a union, not bare ``enum.StrEnum`` with no members). Every member
    ``.value`` must be an exact ``str`` (a ``str`` subclass stays on the
    host) that encodes as UTF-8 (a lone surrogate stays on the host).
    Extra bounds stay on the host. Plain ``EnumValidator`` /
    ``IntegerEnumValidator`` / ``Validator[SomeStrEnum]`` stay on the
    host — this module does not import facades; the facade is the class
    in ``ux_valio.facades.typed``. ``BooleanValidator`` is
    ``_closed_boolean``, not this function.
    """
    if type(owner).__module__ != "ux_valio.facades.typed":
        return None
    if type(owner).__qualname__ != "StringEnumValidator":
        return None
    annotation = getattr(owner, "annotation", None)
    if not isinstance(annotation, type) or not issubclass(annotation, enum.Enum):
        return None
    if annotation is enum.Enum:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    members: list[str] = []
    seen: set[str] = set()
    for member in annotation:
        raw = member.value
        if type(raw) is not str:
            return None
        try:
            raw.encode("utf-8")
        except UnicodeEncodeError:
            return None
        if raw in seen:
            continue
        seen.add(raw)
        members.append(raw)
    if not members:
        return None
    return members


def _closed_boolean(owner: Any) -> dict[str, Any] | None:
    """Empty compile kwargs when the path is exact ``bool`` + the type door.

    Annotation must be ``bool`` (not ``bool | None``, not ``int``). Only
    ``TypeValidator`` may be active. Extra bounds (``min_value``,
    ``required``, choice, ``reassign=False``) stay on the host. No
    coerce: ``1`` / ``0`` are not ``bool``. ``BooleanValidator`` is the
    taught facade; ``Validator[bool]`` with the same closed shape is the
    same door. This module does not import facades.
    """
    if getattr(owner, "annotation", None) is not bool:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {}


def _is_decimal_type_annotation(annotation: Any) -> bool:
    """Exact ``decimal.Decimal``, or the facade coerce union ``Decimal | str``.

    ``Decimal | None`` and every other union stay on the host. This
    module does not import facades.
    """
    if annotation is decimal.Decimal:
        return True
    origin = get_origin(annotation)
    if origin is not Union and not isinstance(annotation, types.UnionType):
        return False
    return frozenset(get_args(annotation)) == frozenset((decimal.Decimal, str))


def _is_date_type_annotation(annotation: Any) -> bool:
    """Exact ``datetime.date``, or the facade coerce union ``date | str``.

    ``date | None`` and every other union stay on the host.
    ``datetime.datetime`` is not this annotation (that is
    ``_is_datetime_type_annotation``). This module does not import
    facades.
    """
    return _is_stored_or_str_annotation(annotation, datetime.date)


def _is_uuid_type_annotation(annotation: Any) -> bool:
    """Exact ``uuid.UUID``, or the facade coerce union ``UUID | str``.

    ``UUID | None`` and every other union stay on the host. This
    module does not import facades.
    """
    return _is_stored_or_str_annotation(annotation, uuid.UUID)


def _is_datetime_type_annotation(annotation: Any) -> bool:
    """Exact ``datetime.datetime``, or the facade coerce union ``datetime | str``.

    ``datetime | None`` and every other union stay on the host. A
    plain ``datetime.date`` annotation is ``_is_date_type_annotation``.
    This module does not import facades.
    """
    return _is_stored_or_str_annotation(annotation, datetime.datetime)


def _is_stored_or_str_annotation(annotation: Any, stored: type) -> bool:
    """Exact ``stored``, or the coerce union ``stored | str``.

    ``stored | None`` and every other union stay on the host.
    """
    if annotation is stored:
        return True
    origin = get_origin(annotation)
    if origin is not Union and not isinstance(annotation, types.UnionType):
        return False
    return frozenset(get_args(annotation)) == frozenset((stored, str))


def _closed_date(owner: Any) -> dict[str, Any] | None:
    """Empty compile kwargs when the path is ``datetime.date`` + the type door.

    Annotation is ``datetime.date`` or the coerce union
    ``datetime.date | str`` (``DateValidator``). Only ``TypeValidator``
    may be active. Extra bounds (``min_value``, ``required``, choice,
    ``reassign=False``) stay on the host. String coerce stays host
    ``_pre_validate``. ``DateValidator`` is the taught facade;
    ``Validator[datetime.date]`` with the same closed shape is the
    same door. This module does not import facades.
    """
    if not _is_date_type_annotation(getattr(owner, "annotation", None)):
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {}


def _closed_uuid(owner: Any) -> dict[str, Any] | None:
    """Empty compile kwargs when the path is ``uuid.UUID`` + the type door.

    Annotation is ``uuid.UUID`` or the coerce union ``uuid.UUID | str``
    (``UUIDValidator``). Only ``TypeValidator`` may be active. Extra
    bounds (``min_value``, ``required``, choice, ``reassign=False``)
    stay on the host. String coerce stays host ``_pre_validate``.
    ``UUIDValidator`` is the taught facade; ``Validator[uuid.UUID]``
    with the same closed shape is the same door. This module does not
    import facades.
    """
    if not _is_uuid_type_annotation(getattr(owner, "annotation", None)):
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {}


def _read_ip_facade(owner: Any) -> tuple[str, Any, str] | None:
    """``(kind, parser, label)`` for a closed IP facade. Else ``None``.

    Kind is the ``compile_ip`` argument (``ipv4`` / ``ipv6`` / ``ip``).
    The parser and label match ``_reject_unless_ip`` on the facade.
    """
    if type(owner).__module__ != "ux_valio.facades.typed":
        return None
    return _IP_FACADES.get(type(owner).__qualname__)


def _closed_ip(owner: Any) -> dict[str, str] | None:
    """Compile kwargs when the path is an IP facade + the type door.

    Annotation must be ``str``. Only ``TypeValidator`` may be active.
    Extra bounds (``max_length``, ``required``, choice, pattern,
    ``reassign=False``) stay on the host. The stored value stays the
    given string: there is no ``_pre_validate`` coerce to
    ``ipaddress`` objects. ``StringValidator`` is not this door.
    """
    spec = _read_ip_facade(owner)
    if spec is None:
        return None
    if getattr(owner, "annotation", None) is not str:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {"kind": spec[0]}


def _closed_datetime(owner: Any) -> dict[str, Any] | None:
    """Empty compile kwargs when the path is ``datetime.datetime`` + the type door.

    Annotation is ``datetime.datetime`` or the coerce union
    ``datetime.datetime | str`` (``DateTimeValidator``). Only
    ``TypeValidator`` may be active. Extra bounds stay on the host.
    String coerce stays host ``_pre_validate``. A plain ``date``
    annotation is ``_closed_date``. This module does not import
    facades.
    """
    if not _is_datetime_type_annotation(getattr(owner, "annotation", None)):
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {}


def _closed_decimal(owner: Any) -> dict[str, Any] | None:
    """Empty compile kwargs when the path is Decimal + the type door.

    Annotation is ``decimal.Decimal`` or the coerce union
    ``decimal.Decimal | str`` (``DecimalValidator``). Only
    ``TypeValidator`` may be active. Extra bounds (``min_value``,
    ``required``, choice, ``reassign=False``) stay on the host. No
    scale kwargs. String coerce stays host ``_pre_validate``; ``float``
    / ``int`` / ``bool`` are not ``Decimal``. ``DecimalValidator`` is
    the taught facade; ``Validator[decimal.Decimal]`` with the same
    closed shape is the same door. This module does not import facades.
    """
    if not _is_decimal_type_annotation(getattr(owner, "annotation", None)):
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {}


def _closed_bytes_length(owner: Any) -> dict[str, int] | None:
    """Compile kwargs when the specified path is Bytes + LengthValidator.

    Annotation must be ``bytes``. Bounds must be ``int`` (not ``bool`` /
    ``float``). Pattern / custom / String stay on the host. Count is
    ``len(bytes)`` (byte length), not Unicode codepoints.
    """
    return _closed_length(owner, bytes)


def _clear_native(owner: Any) -> None:
    """One host-fallback clear for the bind-time native bundle."""
    owner._native_plan = None
    owner._native_apply = None
    owner._native_fail_kind = None
    owner._native_run = None


def _bridge_to_value(owner: Any, value: Any) -> None:
    """Extract miss before native value/bound apply.

    OverflowError is a bridge signal, not a public validation miss and
    not an L1 "overflow" message. Fall through to host
    ``ValueValidator`` (Door A KEEP wording).
    """
    ValueValidator._validate_value(owner, None, value)


def _bridge_to_length(owner: Any, value: Any) -> None:
    """Extract miss before native length apply.

    OverflowError / UnicodeEncodeError / extract TypeError is a bridge
    signal, not a public validation miss and not an L1 "overflow"
    message. Fall through to host ``LengthValidator`` (Door A KEEP
    wording, ``len(str)`` or ``len(bytes)``).
    """
    LengthValidator._validate_length(owner, None, value)


def _bridge_to_ip(owner: Any, value: Any) -> None:
    """Extract miss before native IP apply.

    UnicodeError / extract TypeError on a value the host already
    accepted as ``str`` is a bridge signal, not an L1 "overflow"
    message. Fall through to the same stdlib parser the facade uses
    (``IPv4Address`` / ``IPv6Address`` / ``ip_address``) so the KEEP
    ``ValueError`` wording does not fork.
    """
    spec = _read_ip_facade(owner)
    if spec is None:
        raise RuntimeError("ux_valio_native apply failed")
    _reject_ip_string(owner, value, spec[1], spec[2])


def _reject_ip_string(owner: Any, value: Any, parser: Any, label: str) -> None:
    """KEEP IP ``ValueError`` wording. Same text as ``_reject_unless_ip``."""
    if value is None:
        return
    try:
        parser(value)
    except (ValueError, ipaddress.AddressValueError) as err:
        raise ValueError(
            f"{owner.name} expects a valid {label}, got {value} as value instead"
        ) from err


def _bridge_to_type(owner: Any, value: Any) -> None:
    """Extract miss before native type-door or member-set apply.

    OverflowError / UnicodeError / extract TypeError is a bridge
    signal, not a public validation miss and not an L1 "overflow"
    message. Fall through to host ``TypeValidator`` (Door A KEEP
    wording). A member whose value does not fit the FFI type never
    compiled (bind stays on the host).
    """
    TypeValidator._validate_type(owner, None, value)


def _raise_native_bound_miss(owner: Any, fail: Any, value: Any) -> None:
    """Map native ``FailKind`` to Door A KEEP wording. Unexpected kind is infra."""
    kinds = owner._native_fail_kind
    match fail:
        case kinds.MinValue:
            min_value = owner.min_value
            raise ValueError(
                f"{owner.name} expect the minimum value of {min_value}, "
                f"got {value} instead"
            )
        case kinds.MaxValue:
            max_value = owner.max_value
            raise ValueError(
                f"{owner.name} expect the maximum value of {max_value}, "
                f"got {value} instead"
            )
        case kinds.GreaterThan:
            gt = owner.gt
            raise ValueError(
                f"{owner.name} expect a value greater than {gt}, got {value} instead"
            )
        case kinds.LessThan:
            lt = owner.lt
            raise ValueError(
                f"{owner.name} expect a value less than {lt}, got {value} instead"
            )
        case kinds.Equal:
            of_value = owner.value
            raise ValueError(
                f"{owner.name} expect the value {of_value}, got {value} as value instead"
            )
        case kinds.MinLength:
            min_length = owner.min_length
            raise ValueError(
                f"{owner.name} expect the value of minimum length {min_length}, "
                f"got length {len(value)} value instead"
            )
        case kinds.MaxLength:
            max_length = owner.max_length
            raise ValueError(
                f"{owner.name} expect the value of maximum length {max_length}, "
                f"got length {len(value)} value instead"
            )
        case kinds.Length:
            length = owner.length
            raise ValueError(
                f"{owner.name} expect the value of length {length}, "
                f"got length {len(value)} value instead"
            )
        case kinds.NotMember:
            raise TypeError(
                f"{owner.name} expect {owner.annotation} type, "
                f"got {type(value).__name__} type instead"
            )
        case kinds.NotIp:
            spec = _read_ip_facade(owner)
            if spec is None:
                raise RuntimeError(
                    f"ux_valio_native apply returned unexpected fail kind {fail!r}"
                )
            _reject_ip_string(owner, value, spec[1], spec[2])
            raise RuntimeError(
                f"ux_valio_native apply returned unexpected fail kind {fail!r}"
            )
        case _:
            raise RuntimeError(
                f"ux_valio_native apply returned unexpected fail kind {fail!r}"
            )


def _raise_host_integer_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Integer type door is host-first.

    FFI type is the later ``i64`` extract (bound ``FailKind`` map runs
    after). Python ``True`` is ``int`` (load-bearing) so it never
    reaches here. ``None`` is skipped by the caller. ``collect_all``
    continues into host ``ValueValidator``. Open TypeValidator stays
    on the host — not a native FailKind.
    """
    _raise_host_closed_type_miss(owner, value, ValueValidator._validate_value)


def _raise_host_float_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Float type door is host-first.

    FFI type is the later ``f64`` extract. Python ``int`` / ``bool``
    are not ``float`` (KEEP). ``None`` is skipped by the caller.
    ``collect_all`` continues into host ``ValueValidator``. NaN / ±inf
    are ``float`` and reach apply.
    """
    _raise_host_closed_type_miss(owner, value, ValueValidator._validate_value)


def _raise_host_string_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed String type door is host-first.

    FFI type is the later ``&str`` extract. Python ``bytes`` / ``int``
    are not ``str`` (KEEP). ``None`` is skipped by the caller.
    ``collect_all`` continues into host ``LengthValidator``.
    """
    _raise_host_closed_type_miss(owner, value, LengthValidator._validate_length)


def _raise_host_enum_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording for a closed IntegerEnum or StringEnum plan.

    Closed enum type door is host-first. IntegerEnum FFI type is the
    later ``i64`` extract; StringEnum is ``&str`` of ``value.value``.
    The concrete enum on the field is the member class, so a plain
    ``int`` / ``str`` / ``bool`` / another enum misses here — including
    another enum whose value collides with a member. ``None`` is
    skipped by the caller. ``collect_all`` continues into the named
    enum extra from ``validate``, not inside this raise.
    """
    raise TypeError(
        f"{owner.name} expect {owner.annotation} type, "
        f"got {type(value).__name__} type instead"
    )


def _raise_host_date_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Date type door is host-first.

    FFI type is the later ``datetime.date`` extract. ``int`` / ``str`` /
    ``bool`` miss. A ``datetime.datetime`` is a ``date`` and does not
    miss here (``DateValidator`` rejects it in the named extra). A raw
    ``str`` misses only when the annotation does not accept ``str``;
    the coerce union accepts ``str`` here and ``_pre_validate`` has
    already parsed a calendar string. ``None`` is skipped by the
    caller. The closed plan has no second path unit, so
    ``collect_all`` does not continue inside this raise (``validate``
    still continues into the named extra).
    """
    TypeValidator._validate_type(owner, None, value)


def _raise_host_ip_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed IP type door is host-first.

    FFI type is the later ``str`` extract. ``int`` / ``bytes`` /
    ``ipaddress`` objects miss here. A ``str`` does not. ``None`` is
    skipped by the caller. The closed plan has no second path unit,
    so ``collect_all`` does not continue inside this raise
    (``validate`` still continues into the named extra for a non-str).
    """
    TypeValidator._validate_type(owner, None, value)


def _raise_host_uuid_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Uuid type door is host-first.

    FFI type is the later ``uuid.UUID`` extract. ``int`` / ``bool`` /
    ``bytes`` miss. A raw ``str`` misses only when the annotation
    does not accept ``str``; the coerce union accepts ``str`` here
    and ``_pre_validate`` has already parsed a UUID string. ``None``
    is skipped by the caller. The closed plan has no second path
    unit, so ``collect_all`` does not continue inside this raise
    (``validate`` still continues into the named extra).
    """
    TypeValidator._validate_type(owner, None, value)


def _raise_host_datetime_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed DateTime type door is host-first.

    FFI type is the later ``datetime.datetime`` extract. A plain
    ``datetime.date`` / ``int`` / ``str`` / ``bool`` miss. A raw
    ``str`` misses only when the annotation does not accept ``str``;
    the coerce union accepts ``str`` here and ``_pre_validate`` has
    already parsed an ISO string. ``None`` is skipped by the caller.
    The closed plan has no second path unit, so ``collect_all`` does
    not continue inside this raise (``validate`` still continues into
    the named extra).
    """
    TypeValidator._validate_type(owner, None, value)


def _raise_host_decimal_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Decimal type door is host-first.

    FFI type is the later ``decimal.Decimal`` extract. ``float`` /
    ``int`` / ``bool`` miss (no silent float→Decimal). A raw ``str``
    misses only when the annotation does not accept ``str``; the coerce
    union accepts ``str`` here and the named extra still requires
    ``Decimal``. ``None`` is skipped by the caller. The closed plan has
    no second path unit and no scale unit, so ``collect_all`` does not
    continue inside this raise (``validate`` still continues into the
    named extra).
    """
    TypeValidator._validate_type(owner, None, value)


def _raise_host_boolean_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Boolean type door is host-first.

    FFI type is the later ``bool`` extract. Python ``int`` (``1`` /
    ``0``) is not ``bool`` (KEEP; no coerce). ``None`` is skipped by
    the caller. The closed plan has no second path unit, so
    ``collect_all`` does not continue inside this raise.
    """
    raise TypeError(
        f"{owner.name} expect {owner.annotation} type, "
        f"got {type(value).__name__} type instead"
    )


def _raise_host_bytes_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Bytes type door is host-first.

    FFI type is the later ``&[u8]`` extract. Python ``str`` /
    ``bytearray`` / ``int`` are not ``bytes`` (KEEP). ``None`` is
    skipped by the caller. ``collect_all`` continues into host
    ``LengthValidator``.
    """
    _raise_host_closed_type_miss(owner, value, LengthValidator._validate_length)


def _raise_host_closed_type_miss(owner: Any, value: Any, continue_unit: Any) -> None:
    """KEEP TypeError wording for a closed Integer, Float, String, or Bytes plan."""
    err = TypeError(
        f"{owner.name} expect {owner.annotation} type, "
        f"got {type(value).__name__} type instead"
    )
    if not owner.collect_all:
        raise err
    errors: list[BaseException] = [err]
    try:
        continue_unit(owner, None, value)
    except Exception as second:
        errors.append(second)
    raise_collected(errors, name=owner.name)


def _bind_compiled_plan(
    owner: Any, native: Any, compile_fn: Any, bounds: dict[str, Any]
) -> None:
    try:
        owner._native_plan = compile_fn(**bounds)
        owner._native_fail_kind = native.FailKind
    except OverflowError:
        _clear_native(owner)
        return
    except Exception as err:
        _clear_native(owner)
        raise RuntimeError("ux_valio_native bind failed") from err


def _apply_native_closed(
    owner: Any,
    value: Any,
    expected: type,
    raise_type_miss: Any,
    after_overflow: Any,
    extract_errors: type[BaseException] | tuple[type[BaseException], ...] = OverflowError,
) -> None:
    """One FFI apply. Host formats KEEP wording. Extract overflow stays on host."""
    if value is None:
        return
    if not isinstance(value, expected):
        raise_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except extract_errors:
        after_overflow(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_integer_bounds(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Out-of-i64 ints stay on host."""
    _apply_native_closed(
        owner,
        value,
        int,
        _raise_host_integer_type_miss,
        _bridge_to_value,
    )


def apply_native_float_bounds(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. f64 extract miss stays on host.

    OverflowError at ``f64`` extract is a bridge signal (same three
    buckets as Integer: validation / bridge / native-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A NaN/inf is IEEE compare, not a fourth
    bucket.
    """
    _apply_native_closed(
        owner,
        value,
        float,
        _raise_host_float_type_miss,
        _bridge_to_value,
    )


def apply_native_string_length(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. UTF-8 extract miss stays on host.

    OverflowError / UnicodeEncodeError at ``&str`` extract is a bridge
    signal (same three buckets as Integer/Float: validation / bridge /
    native-infra ``RuntimeError`` naming ``ux_valio_native``). No public
    L1 "overflow" message. Door A length is ``len(str)`` codepoints.
    """
    _apply_native_closed(
        owner,
        value,
        str,
        _raise_host_string_type_miss,
        _bridge_to_length,
        (OverflowError, UnicodeError),
    )


def apply_native_string_enum(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-UTF-8 stays on host.

    The FFI argument is ``value.value`` (UTF-8 ``&str``), not the enum
    object. OverflowError / UnicodeError at ``&str`` extract is a
    bridge signal (same three buckets as String length: validation
    ``FailKind`` / bridge / native-infra ``RuntimeError`` naming
    ``ux_valio_native``). No public L1 "overflow" message. Door A
    membership is the concrete enum class first, then exact UTF-8
    equality with the compiled member values.
    """
    if value is None:
        return
    if not isinstance(value, owner.annotation):
        _raise_host_enum_type_miss(owner, value)
        return
    raw = value.value
    if type(raw) is not str:
        _bridge_to_type(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, raw)
    except (OverflowError, UnicodeError):
        _bridge_to_type(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_integer_enum(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Out-of-i64 ints stay on host.

    OverflowError at ``i64`` extract is a bridge signal (same three
    buckets as Integer: validation ``FailKind`` / bridge / native-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A membership is the concrete enum class
    first, then exact ``i64`` equality with the compiled member values.
    """
    _apply_native_closed(
        owner,
        value,
        owner.annotation,
        _raise_host_enum_type_miss,
        _bridge_to_type,
    )


def apply_native_bytes_length(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. bytes extract miss stays on host.

    OverflowError / extract TypeError at ``&[u8]`` extract is a bridge
    signal (same three buckets as Integer/Float/String: validation /
    bridge / native-infra ``RuntimeError`` naming ``ux_valio_native``).
    No public L1 "overflow" message. Door A length is ``len(bytes)``.
    """
    _apply_native_closed(
        owner,
        value,
        bytes,
        _raise_host_bytes_type_miss,
        _bridge_to_length,
        (OverflowError, TypeError),
    )


def apply_native_date(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-date stays on host.

    TypeError at ``datetime.date`` extract is a bridge signal (same
    three buckets as Decimal: validation ``FailKind`` / bridge /
    native-infra ``RuntimeError`` naming ``ux_valio_native``). No
    public L1 "overflow" message. Door A is ``datetime.date`` after
    host string coerce. ``datetime.datetime`` passes this extract
    (subclass) and ``DateValidator`` still rejects it afterwards. No
    bound unit.
    """
    if value is None:
        return
    if not isinstance(value, datetime.date):
        _raise_host_date_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except TypeError:
        _bridge_to_type(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_uuid(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-UUID stays on host.

    TypeError at ``uuid.UUID`` extract is a bridge signal (same three
    buckets as Date: validation ``FailKind`` / bridge / native-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A is ``uuid.UUID`` after host string
    coerce. ``int`` / ``bool`` / ``bytes`` miss. No bound unit.
    """
    if value is None:
        return
    if not isinstance(value, uuid.UUID):
        _raise_host_uuid_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except TypeError:
        _bridge_to_type(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_ip(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-str stays on host.

    UnicodeError / TypeError at ``str`` extract is a bridge signal
    (same three buckets as String length: validation ``FailKind`` /
    bridge / native-infra ``RuntimeError`` naming ``ux_valio_native``).
    No public L1 "overflow" message. Door A is the given string: a
    valid address passes and is stored unchanged; an invalid address
    is ``FailKind.NotIp``. ``int`` / ``bytes`` are not coerced. No
    bound unit.
    """
    if value is None:
        return
    if not isinstance(value, str):
        _raise_host_ip_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except (UnicodeError, OverflowError, TypeError):
        _bridge_to_ip(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_datetime(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-datetime stays on host.

    TypeError at ``datetime.datetime`` extract is a bridge signal (same
    three buckets as Date: validation ``FailKind`` / bridge /
    native-infra ``RuntimeError`` naming ``ux_valio_native``). No
    public L1 "overflow" message. Door A is ``datetime.datetime`` after
    host string coerce. A plain ``datetime.date`` misses. No bound unit.
    """
    if value is None:
        return
    if not isinstance(value, datetime.datetime):
        _raise_host_datetime_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except TypeError:
        _bridge_to_type(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_decimal(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-Decimal stays on host.

    TypeError at ``decimal.Decimal`` extract is a bridge signal (same
    three buckets as Boolean: validation ``FailKind`` / bridge /
    native-infra ``RuntimeError`` naming ``ux_valio_native``). No public
    L1 "overflow" message. Door A is exact ``decimal.Decimal`` after
    host string coerce: ``float`` / ``int`` / ``bool`` do not coerce.
    No scale unit. No bound unit.
    """
    if value is None:
        return
    if not isinstance(value, decimal.Decimal):
        _raise_host_decimal_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except TypeError:
        _bridge_to_type(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_boolean(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-bool stays on host.

    TypeError at ``bool`` extract is a bridge signal (same three
    buckets as Integer: validation ``FailKind`` / bridge / native-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A is exact ``bool``: ``True`` and
    ``False`` pass; ``1`` and ``0`` do not coerce. No bound unit.
    """
    _apply_native_closed(
        owner,
        value,
        bool,
        _raise_host_boolean_type_miss,
        _bridge_to_type,
        TypeError,
    )


def apply_native_bounds(owner: Any, value: Any) -> None:
    """Call the bind-time family run. Unset bundle is a caller bug.

    ``_native_apply`` is the product-PyO3 Rust FFI. ``_native_run`` is
    the closed-family Python entry (``apply_native_integer_bounds`` and
    the other family doors).
    """
    run = owner._native_run
    if run is None:
        raise RuntimeError("ux_valio_native apply failed")
    run(owner, value)


type _ClosedPair = tuple[Any, Any, Any, dict[str, Any]]


def _select_integer_bounds(native: Any, bounds: dict[str, int]) -> _ClosedPair:
    """Closed Integer: ``compile_integer`` and ``apply_integer`` stay a pair."""
    return (
        native.apply_integer,
        apply_native_integer_bounds,
        native.compile_integer,
        bounds,
    )


def _select_float_bounds(native: Any, bounds: dict[str, float]) -> _ClosedPair:
    """Closed Float: ``compile_float`` and ``apply_float`` stay a pair."""
    return (
        native.apply_float,
        apply_native_float_bounds,
        native.compile_float,
        bounds,
    )


def _select_string_length(native: Any, bounds: dict[str, int]) -> _ClosedPair:
    """Closed String: ``compile_string`` and ``apply_string`` stay a pair."""
    return (
        native.apply_string,
        apply_native_string_length,
        native.compile_string,
        bounds,
    )


def _select_bytes_length(native: Any, bounds: dict[str, int]) -> _ClosedPair:
    """Closed Bytes: ``compile_bytes`` and ``apply_bytes`` stay a pair."""
    return (
        native.apply_bytes,
        apply_native_bytes_length,
        native.compile_bytes,
        bounds,
    )


def _select_integer_enum(native: Any, members: list[int]) -> _ClosedPair:
    """Closed IntegerEnum: ``compile_integer_enum`` / ``apply_integer_enum`` stay a pair."""
    return (
        native.apply_integer_enum,
        apply_native_integer_enum,
        native.compile_integer_enum,
        {"members": members},
    )


def _select_boolean(native: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed Boolean: ``compile_boolean`` and ``apply_boolean`` stay a pair."""
    return (
        native.apply_boolean,
        apply_native_boolean,
        native.compile_boolean,
        bounds,
    )


def _select_date(native: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed Date: ``compile_date`` and ``apply_date`` stay a pair."""
    return (
        native.apply_date,
        apply_native_date,
        native.compile_date,
        bounds,
    )


def _select_uuid(native: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed Uuid: ``compile_uuid`` and ``apply_uuid`` stay a pair."""
    return (
        native.apply_uuid,
        apply_native_uuid,
        native.compile_uuid,
        bounds,
    )


def _select_ip(native: Any, bounds: dict[str, str]) -> _ClosedPair:
    """Closed IP: ``compile_ip`` and ``apply_ip`` stay a pair."""
    return (
        native.apply_ip,
        apply_native_ip,
        native.compile_ip,
        bounds,
    )


def _select_datetime(native: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed DateTime: ``compile_datetime`` and ``apply_datetime`` stay a pair."""
    return (
        native.apply_datetime,
        apply_native_datetime,
        native.compile_datetime,
        bounds,
    )


def _select_decimal(native: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed Decimal: ``compile_decimal`` and ``apply_decimal`` stay a pair."""
    return (
        native.apply_decimal,
        apply_native_decimal,
        native.compile_decimal,
        bounds,
    )


def _select_string_enum(native: Any, members: list[str]) -> _ClosedPair:
    """Closed StringEnum: ``compile_string_enum`` / ``apply_string_enum`` stay a pair."""
    return (
        native.apply_string_enum,
        apply_native_string_enum,
        native.compile_string_enum,
        {"members": members},
    )


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No native module / unclosed path → ``_native_plan is None``.

    One walk. Each closed family keeps its own ``compile_*`` / ``apply_*``
    pair: Integer / Float own ``BoundUnit`` values, String / Bytes own
    ``LengthUnit`` values, IntegerEnum / StringEnum own a member set,
    Boolean / Decimal / Date / DateTime / Uuid are type-door markers.
    IP owns an address kind and checks a ``str``. An
    unclosed path does not import the extra. Do not merge a pair into
    one door.
    """
    families: tuple[tuple[Any, Any], ...] = (
        (_closed_integer_bounds, _select_integer_bounds),
        (_closed_float_bounds, _select_float_bounds),
        (_closed_string_length, _select_string_length),
        (_closed_bytes_length, _select_bytes_length),
        (_closed_integer_enum_members, _select_integer_enum),
        (_closed_string_enum_members, _select_string_enum),
        (_closed_boolean, _select_boolean),
        (_closed_decimal, _select_decimal),
        (_closed_date, _select_date),
        (_closed_datetime, _select_datetime),
        (_closed_uuid, _select_uuid),
        (_closed_ip, _select_ip),
    )
    for detect, select in families:
        payload = detect(owner)
        if payload is None:
            continue
        native = _load_native()
        if native is None:
            _clear_native(owner)
            return
        apply, run, compile_fn, kwargs = select(native, payload)
        owner._native_apply = apply
        owner._native_run = run
        _bind_compiled_plan(owner, native, compile_fn, kwargs)
        return
    _clear_native(owner)
