# SPDX-License-Identifier: MIT
"""Optional native apply (product PyO3 ``ux_valio_native``). Not a taught import.

One module. A private split is worth it only when opening that file
shows one family's walk and nothing else. Shared detectors, bridges,
and the bind table still serve every family, so they stay here.
Each Door A family is one contiguous section. ``bind_native_plan``
walks ``_FAMILY_DOORS`` (a private frozen ``_FamilyDoor`` row:
``closed`` / ``compile`` / ``apply`` / ``run`` / ``extract``, and
``expected`` / ``type_miss`` / ``bridge`` / ``extract_errors``
when apply is ``_run_closed``). Bind calls that row's ``_select``.
Every closed family stores ``door._run_closed`` on ``_native_run``.
``extract`` is identity except StringEnum, which passes
``attrgetter("value")`` so apply receives the member string.
Constant closed detectors are ``functools.partial`` of the shared
helper. Decimal, Date, DateTime, Uuid, IP, and Path share
``_raise_host_type_door_miss``. There is no per-family
``_select_*`` and no shell in front of ``_run_closed``.
That row is not a product type door and not a class-per-type
mirror of Rust ``Plan``. This is not a ``plan`` / ``bound`` /
``length`` mirror of the Rust crate.

``Plan`` is one variant per family. Integer / Float own ``BoundUnit``
values. String / Bytes own ``LengthUnit`` values. IntegerEnum /
StringEnum own a member set. Boolean / Decimal / Date / DateTime /
Uuid / Path are type-door markers. IP owns an address kind
(``ipv4`` / ``ipv6`` / ``ip``) and checks a ``str``. There is no
shared unit bag.

Bind-time choice: when ``ux_valio_native`` is importable and the
specified path is one closed family, compile that variant once.
Type door is host-first ``isinstance`` then FFI extract (``i64`` /
``f64`` / ``&str`` / ``&[u8]`` / ``bool`` / ``decimal.Decimal`` /
``datetime.date`` / ``datetime.datetime`` / ``uuid.UUID`` /
``pathlib.Path`` / ``str`` for IP);
bound / length / member checks run after extract. StringEnum
``extract`` is ``attrgetter("value")`` (UTF-8 ``&str`` of the
member). Boolean extract is exact ``bool`` (``1`` / ``0`` are not
coerced). Decimal
extract is exact ``decimal.Decimal`` (``float`` / ``int`` /
``bool`` are not coerced; string coerce stays host
``_pre_validate``). No scale unit. Date extract is
``datetime.date`` (a ``datetime.datetime`` extracts, because it
subclasses ``date``; ``DateValidator`` still rejects it in the
named extra). DateTime extract is ``datetime.datetime`` (a plain
``date`` does not). Uuid extract is ``uuid.UUID`` (a raw ``str``
does not). Path extract is ``pathlib.Path`` (a raw ``str`` does
not; ``pathlib.PurePath`` does not). String coerce for Date,
DateTime, Uuid, and Path stays host ``_pre_validate``.
``path_exists`` stays host. IP facades do not coerce: the stored
value is the given string, and ``apply_ip`` mirrors
``ipaddress.IPv4Address`` / ``IPv6Address`` / ``ip_address`` on
that string (``FailKind.NotIp``).
Open TypeValidator / Union / TypedDict /
Annotated / pattern / plain ``EnumValidator``
stay on the host. A ``BooleanValidator``, ``DecimalValidator``,
``DateValidator``, ``DateTimeValidator``, ``UUIDValidator``,
``PathValidator``, ``IPv4Validator``, ``IPv6Validator``, or
``IPAddressValidator`` with any extra unit stays on the host.
Missing or failed extra → host
``_active_units`` path. No import on the hot path after that
choice. Each family keeps its own ``compile_*`` / ``apply_*`` pair.
Not Cap Door B.
"""

from __future__ import annotations

import datetime
import decimal
import enum
import ipaddress
import pathlib
import types
import uuid
from functools import partial
from operator import attrgetter
from typing import Any, NamedTuple, Union, get_args, get_origin

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


def _closed_type_door(owner: Any, annotation_matches: Any) -> dict[str, Any] | None:
    """Empty compile kwargs when only the type door is active.

    ``annotation_matches`` is the family annotation check. Extra
    units stay on the host. The dict is the compile payload (no
    bound, no member set).
    """
    if not annotation_matches(getattr(owner, "annotation", None)):
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    return {}


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


def _recompile_closed_owners(owner: Any) -> None:
    """Refresh sealed set-phase lists after a plan bind or clear."""
    closed = getattr(owner, "_closed", None)
    recompile = getattr(owner, "_recompile_closed", None)
    if not closed or not callable(recompile):
        return
    recompile(tuple(closed))


def _clear_native(owner: Any) -> None:
    """One host-fallback clear for the bind-time native bundle."""
    owner._native_plan = None
    owner._native_apply = None
    owner._native_fail_kind = None
    owner._native_run = None
    _recompile_closed_owners(owner)


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


def _raise_host_value_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording for a closed Integer or Float plan.

    Closed type door is host-first. Integer FFI type is the later
    ``i64`` extract; Float is ``f64``. Python ``True`` is ``int``
    (load-bearing) so an Integer plan never reaches this raise for
    ``True``. ``int`` / ``bool`` are not ``float``. NaN / ±inf are
    ``float`` and reach apply. ``None`` is skipped by the caller.
    ``collect_all`` continues into host ``ValueValidator``. Open
    TypeValidator stays on the host — not a native FailKind.
    """
    _raise_host_closed_type_miss(owner, value, ValueValidator._validate_value)


def _raise_host_length_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording for a closed String or Bytes plan.

    Closed type door is host-first. String FFI type is the later
    ``&str`` extract; Bytes is ``&[u8]``. ``bytes`` is not ``str``.
    ``str`` / ``bytearray`` are not ``bytes``. ``None`` is skipped
    by the caller. ``collect_all`` continues into host
    ``LengthValidator``.
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
    enum extra from ``validate``, not inside this raise. This raise
    does not enter ``TypeValidator`` (Boolean is the same class of
    miss). Do not fold it into ``_raise_host_type_door_miss``.
    """
    raise TypeError(
        f"{owner.name} expect {owner.annotation} type, "
        f"got {type(value).__name__} type instead"
    )


def _raise_host_type_door_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording for a closed type door that only forwards.

    Decimal, Date, DateTime, Uuid, IP, and Path call
    ``TypeValidator._validate_type``. The sentence matches that door.
    ``collect_all`` does not continue inside this raise (``validate``
    still continues into a named extra). Boolean and enum keep their
    own raises.
    """
    TypeValidator._validate_type(owner, None, value)


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


def _read_owner_annotation(owner: Any) -> Any:
    """Host isinstance type when the closed plan stores the annotation."""
    return owner.annotation


def _extract_same(value: Any) -> Any:
    """Identity payload. StringEnum overrides this with member ``.value``."""
    return value


type _ClosedPair = tuple[Any, Any, Any, dict[str, Any]]


class _FamilyDoor(NamedTuple):
    """Private bind row for one closed family. Not a product type door.

    ``closed`` detects the family. ``compile`` / ``apply`` name the
    Rust pair. Omitted ``run`` means bind stores this row's
    ``_run_closed``. ``extract`` maps the host value to the FFI
    payload (identity, or ``attrgetter("value")`` for StringEnum).
    ``expected`` is the host ``isinstance`` type, or a callable of
    ``owner`` when that type is the annotation (IntegerEnum /
    StringEnum). ``type_miss`` formats the KEEP TypeError.
    ``bridge`` is the extract-miss fallthrough. ``extract_errors``
    are the FFI signals that bridge. A member list is compile
    kwargs ``members=``; any other payload is already those kwargs.
    """

    closed: Any
    compile: str
    apply: str
    run: Any = None
    expected: Any = None
    type_miss: Any = None
    bridge: Any = None
    extract_errors: Any = OverflowError
    extract: Any = _extract_same

    def _select(self, native: Any, payload: Any) -> _ClosedPair:
        """Pair for this row. Compile and apply stay separate."""
        kwargs: dict[str, Any]
        if isinstance(payload, list):
            kwargs = {"members": payload}
        else:
            kwargs = payload
        return (
            getattr(native, self.apply),
            self.run,
            getattr(native, self.compile),
            kwargs,
        )

    def _run_closed(self, owner: Any, value: Any) -> None:
        """One FFI apply. Host formats KEEP wording. Extract miss stays on host."""
        if value is None:
            return
        expected = self.expected
        if not isinstance(expected, type):
            expected = expected(owner)
        if not isinstance(value, expected):
            self.type_miss(owner, value)
            return
        extract = self.extract
        payload = value if extract is _extract_same else extract(value)
        try:
            fail = owner._native_apply(owner._native_plan, payload)
        except self.extract_errors:
            self.bridge(owner, value)
            return
        except Exception as err:
            raise RuntimeError("ux_valio_native apply failed") from err
        if fail is None:
            return
        _raise_native_bound_miss(owner, fail, value)


# --- Integer ---


_INTEGER_DOOR = _FamilyDoor(
    closed=partial(_closed_value_bounds, annotation=int, bound_type=int),
    compile="compile_integer",
    apply="apply_integer",
    expected=int,
    type_miss=_raise_host_value_type_miss,
    bridge=_bridge_to_value,
    extract_errors=OverflowError,
)


# --- Float ---


# Bounds must be ``float`` (not ``int``). NaN / ±inf are ``float`` and compile.
_FLOAT_DOOR = _FamilyDoor(
    closed=partial(_closed_value_bounds, annotation=float, bound_type=float),
    compile="compile_float",
    apply="apply_float",
    expected=float,
    type_miss=_raise_host_value_type_miss,
    bridge=_bridge_to_value,
    extract_errors=OverflowError,
)


# --- String ---


# Annotation ``str``. Count is ``len(str)`` codepoints.
_STRING_DOOR = _FamilyDoor(
    closed=partial(_closed_length, annotation=str),
    compile="compile_string",
    apply="apply_string",
    expected=str,
    type_miss=_raise_host_length_type_miss,
    bridge=_bridge_to_length,
    extract_errors=(OverflowError, UnicodeError),
)


# --- Bytes ---


# Annotation ``bytes``. Count is ``len(bytes)``, not Unicode codepoints.
_BYTES_DOOR = _FamilyDoor(
    closed=partial(_closed_length, annotation=bytes),
    compile="compile_bytes",
    apply="apply_bytes",
    expected=bytes,
    type_miss=_raise_host_length_type_miss,
    bridge=_bridge_to_length,
    extract_errors=(OverflowError, TypeError),
)


# --- IntegerEnum ---


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


_INTEGER_ENUM_DOOR = _FamilyDoor(
    closed=_closed_integer_enum_members,
    compile="compile_integer_enum",
    apply="apply_integer_enum",
    expected=_read_owner_annotation,
    type_miss=_raise_host_enum_type_miss,
    bridge=_bridge_to_type,
    extract_errors=OverflowError,
)


# --- StringEnum ---


def _closed_string_enum_members(owner: Any) -> list[str] | None:
    """UTF-8 member values when the path is ``StringEnumValidator`` + type.

    Annotation must be a concrete ``enum.Enum`` (not ``enum.Enum`` itself,
    not a union, not bare ``enum.StrEnum`` with no members). Every member
    ``.value`` must be an exact ``str`` (a ``str`` subclass stays on the
    host) that encodes as UTF-8 (a lone surrogate stays on the host).
    Extra bounds stay on the host. Plain ``EnumValidator`` /
    ``IntegerEnumValidator`` / ``Validator[SomeStrEnum]`` stay on the
    host — this module does not import facades; the facade is the class
    in ``ux_valio.facades.typed``. ``BooleanValidator`` is the
    Boolean type door, not this function.
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


_STRING_ENUM_DOOR = _FamilyDoor(
    closed=_closed_string_enum_members,
    compile="compile_string_enum",
    apply="apply_string_enum",
    expected=_read_owner_annotation,
    type_miss=_raise_host_enum_type_miss,
    bridge=_bridge_to_type,
    extract_errors=(OverflowError, UnicodeError),
    extract=attrgetter("value"),
)


# --- Boolean ---


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


# Annotation must be ``bool`` (not ``bool | None``, not ``int``).
# ``1`` / ``0`` are not ``bool``.
_BOOLEAN_DOOR = _FamilyDoor(
    closed=partial(
        _closed_type_door,
        annotation_matches=lambda annotation: annotation is bool,
    ),
    compile="compile_boolean",
    apply="apply_boolean",
    expected=bool,
    type_miss=_raise_host_boolean_type_miss,
    bridge=_bridge_to_type,
    extract_errors=TypeError,
)


# --- Decimal ---


def _is_decimal_type_annotation(annotation: Any) -> bool:
    """Exact ``decimal.Decimal``, or the facade coerce union ``Decimal | str``.

    ``Decimal | None`` and every other union stay on the host. This
    module does not import facades.
    """
    return _is_stored_or_str_annotation(annotation, decimal.Decimal)


_DECIMAL_DOOR = _FamilyDoor(
    closed=partial(_closed_type_door, annotation_matches=_is_decimal_type_annotation),
    compile="compile_decimal",
    apply="apply_decimal",
    expected=decimal.Decimal,
    type_miss=_raise_host_type_door_miss,
    bridge=_bridge_to_type,
    extract_errors=TypeError,
)


# --- Date ---


def _is_date_type_annotation(annotation: Any) -> bool:
    """Exact ``datetime.date``, or the facade coerce union ``date | str``.

    ``date | None`` and every other union stay on the host.
    ``datetime.datetime`` is not this annotation (that is
    ``_is_datetime_type_annotation``). This module does not import
    facades.
    """
    return _is_stored_or_str_annotation(annotation, datetime.date)


_DATE_DOOR = _FamilyDoor(
    closed=partial(_closed_type_door, annotation_matches=_is_date_type_annotation),
    compile="compile_date",
    apply="apply_date",
    expected=datetime.date,
    type_miss=_raise_host_type_door_miss,
    bridge=_bridge_to_type,
    extract_errors=TypeError,
)


# --- DateTime ---


def _is_datetime_type_annotation(annotation: Any) -> bool:
    """Exact ``datetime.datetime``, or the facade coerce union ``datetime | str``.

    ``datetime | None`` and every other union stay on the host. A
    plain ``datetime.date`` annotation is ``_is_date_type_annotation``.
    This module does not import facades.
    """
    return _is_stored_or_str_annotation(annotation, datetime.datetime)


_DATETIME_DOOR = _FamilyDoor(
    closed=partial(_closed_type_door, annotation_matches=_is_datetime_type_annotation),
    compile="compile_datetime",
    apply="apply_datetime",
    expected=datetime.datetime,
    type_miss=_raise_host_type_door_miss,
    bridge=_bridge_to_type,
    extract_errors=TypeError,
)


# --- UUID ---


def _is_uuid_type_annotation(annotation: Any) -> bool:
    """Exact ``uuid.UUID``, or the facade coerce union ``UUID | str``.

    ``UUID | None`` and every other union stay on the host. This
    module does not import facades.
    """
    return _is_stored_or_str_annotation(annotation, uuid.UUID)


_UUID_DOOR = _FamilyDoor(
    closed=partial(_closed_type_door, annotation_matches=_is_uuid_type_annotation),
    compile="compile_uuid",
    apply="apply_uuid",
    expected=uuid.UUID,
    type_miss=_raise_host_type_door_miss,
    bridge=_bridge_to_type,
    extract_errors=TypeError,
)


# --- IP ---


# Living IP facades store ``str``. The stdlib types are the parsers,
# not the stored type. This module does not import facades; the class
# is the one in ``ux_valio.facades.typed``.
_IP_FACADES = {
    "IPv4Validator": ("ipv4", ipaddress.IPv4Address, "IPv4 address"),
    "IPv6Validator": ("ipv6", ipaddress.IPv6Address, "IPv6 address"),
    "IPAddressValidator": ("ip", ipaddress.ip_address, "IP address"),
}


def _read_ip_facade(owner: Any) -> tuple[str, Any, str] | None:
    """``(kind, parser, label)`` for a closed IP facade. Else ``None``.

    Kind is the ``compile_ip`` argument (``ipv4`` / ``ipv6`` / ``ip``).
    The parser and label match ``_reject_unless_ip`` on the facade.
    """
    if type(owner).__module__ != "ux_valio.facades.typed":
        return None
    return _IP_FACADES.get(type(owner).__qualname__)


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


def _closed_ip(owner: Any) -> dict[str, str] | None:
    """Compile kwargs when the path is an IP facade + the type door.

    Annotation must be ``str``. Only ``TypeValidator`` may be active.
    Extra bounds (``max_length``, ``required``, choice, pattern,
    ``reassign=False``) stay on the host. The stored value stays the
    given string: there is no ``_pre_validate`` coerce to
    ``ipaddress`` objects. An invalid string is ``FailKind.NotIp``;
    the host formats the KEEP ``ValueError``. ``StringValidator``
    is not this door.
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


_IP_DOOR = _FamilyDoor(
    closed=_closed_ip,
    compile="compile_ip",
    apply="apply_ip",
    expected=str,
    type_miss=_raise_host_type_door_miss,
    bridge=_bridge_to_ip,
    extract_errors=(UnicodeError, OverflowError, TypeError),
)


# --- Path ---


def _is_path_type_annotation(annotation: Any) -> bool:
    """Exact ``pathlib.Path``, or the facade coerce union ``Path | str``.

    ``Path | None`` and every other union stay on the host.
    ``pathlib.PurePath`` is not this annotation. This module does not
    import facades.
    """
    return _is_stored_or_str_annotation(annotation, pathlib.Path)


_PATH_DOOR = _FamilyDoor(
    closed=partial(_closed_type_door, annotation_matches=_is_path_type_annotation),
    compile="compile_path",
    apply="apply_path",
    expected=pathlib.Path,
    type_miss=_raise_host_type_door_miss,
    bridge=_bridge_to_type,
    extract_errors=TypeError,
)


# --- Bind walk ---


_FAMILY_DOORS: tuple[_FamilyDoor, ...] = (
    _INTEGER_DOOR,
    _FLOAT_DOOR,
    _STRING_DOOR,
    _BYTES_DOOR,
    _INTEGER_ENUM_DOOR,
    _STRING_ENUM_DOOR,
    _BOOLEAN_DOOR,
    _DECIMAL_DOOR,
    _DATE_DOOR,
    _DATETIME_DOOR,
    _UUID_DOOR,
    _IP_DOOR,
    _PATH_DOOR,
)


def apply_native_bounds(owner: Any, value: Any) -> None:
    """Call the bind-time family run. Unset bundle is a caller bug.

    ``_native_apply`` is the product-PyO3 Rust FFI. ``_native_run`` is
    the closed-family Python entry (``_FamilyDoor._run_closed``).
    StringEnum ``extract`` passes ``value.value`` into that apply.
    """
    run = owner._native_run
    if run is None:
        raise RuntimeError("ux_valio_native apply failed")
    run(owner, value)


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No native module / unclosed path → ``_native_plan is None``.

    One walk over ``_FAMILY_DOORS``. ``door._select`` is that row.
    There is no per-family ``_select_*``. Each closed family keeps
    its own ``compile_*`` / ``apply_*`` pair: Integer / Float own
    ``BoundUnit`` values, String / Bytes own ``LengthUnit`` values,
    IntegerEnum / StringEnum own a member set, Boolean / Decimal /
    Date / DateTime / Uuid / Path are type-door markers. IP owns an
    address kind and checks a ``str``. An unclosed path does not
    import the extra. Do not merge a pair into one door.
    """
    for door in _FAMILY_DOORS:
        payload = door.closed(owner)
        if payload is None:
            continue
        native = _load_native()
        if native is None:
            _clear_native(owner)
            return
        apply, run, compile_fn, kwargs = door._select(native, payload)
        owner._native_apply = apply
        if run is None:
            owner._native_run = door._run_closed
        else:
            owner._native_run = run
        _bind_compiled_plan(owner, native, compile_fn, kwargs)
        if owner._native_plan is not None:
            _recompile_closed_owners(owner)
        return
    _clear_native(owner)
