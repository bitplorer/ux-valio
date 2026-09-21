# SPDX-License-Identifier: MIT
"""Optional native apply peer. Not a taught import.

Bind-time choice: when ``ux_valio_native`` is importable and the specified
path is a closed Integer or Float bound plan (``int`` / ``float``
annotation + only ``ValueValidator`` bounds: min/max/gt/lt/eq), a
closed String or Bytes length plan (``str`` / ``bytes`` annotation +
only ``LengthValidator`` ``min_length`` / ``max_length`` / ``length``),
or a closed IntegerEnum member set (``IntegerEnumValidator`` whose
annotation is a concrete ``enum.IntEnum`` and only the type unit is
active), compile a plan once. Type door is host-first ``isinstance``
then FFI extract (``i64`` / ``f64`` / ``&str`` / ``&[u8]``); bound /
length / member units run after extract. Open TypeValidator / Union /
TypedDict / Annotated / pattern / plain Enum / StringEnum stay on the
host. Missing or failed extra → host ``_active_units`` path. No import
on the hot path after that choice. Not Cap Door B.
"""

from __future__ import annotations

import enum
from typing import Any

from ux_valio.errors import raise_collected
from ux_valio.validators.leaves import TypeValidator
from ux_valio.validators.length import LengthValidator
from ux_valio.validators.value import ValueValidator

_peer: Any | None = None
_probed = False

# Host stores ``eq=`` as ``value``. Compile kwargs use the unit name.
_HOST_BOUND_TO_COMPILE = (
    ("min_value", "min_value"),
    ("gt", "gt"),
    ("max_value", "max_value"),
    ("lt", "lt"),
    ("value", "eq"),
)

# L1 kwargs stay min_length / max_length / length.
_HOST_LENGTH_TO_COMPILE = (
    ("min_length", "min_length"),
    ("max_length", "max_length"),
    ("length", "length"),
)


def _load_native_peer() -> Any | None:
    """Import the extra once. Failed install is host apply, not a hot-path error."""
    global _peer, _probed
    if _probed:
        return _peer
    try:
        import ux_valio_native as peer
    except ImportError:
        _probed = True
        _peer = None
        return None
    except Exception as err:
        raise RuntimeError("ux_valio_native import failed") from err
    _probed = True
    _peer = peer
    return _peer


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
    """Member i64s when the field is a closed ``IntegerEnumValidator`` plan.

    The class marker keeps plain ``EnumValidator``, ``StringEnumValidator``,
    and open ``Validator[SomeIntEnum]`` on the host. Annotation must be a
    concrete ``enum.IntEnum`` subclass (not ``enum.IntEnum`` itself, not
    ``IntFlag``). Only the type unit is active. Member values must be
    ``int`` (``bool`` normalizes to ``0`` / ``1``). An empty member list
    stays on the host. Out-of-i64 values fail later at compile and the
    plan is dropped.
    """
    if getattr(type(owner), "_closed_integer_enum", False) is not True:
        return None
    annotation = getattr(owner, "annotation", None)
    if not isinstance(annotation, type) or annotation is enum.IntEnum:
        return None
    try:
        if not issubclass(annotation, enum.IntEnum) or issubclass(annotation, enum.IntFlag):
            return None
    except TypeError:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (TypeValidator._validate_type,):
        return None
    members: list[int] = []
    seen: set[int] = set()
    for member in annotation:
        raw = member.value
        if type(raw) is bool:
            number = int(raw)
        elif type(raw) is int:
            number = raw
        else:
            return None
        if number in seen:
            continue
        seen.add(number)
        members.append(number)
    if not members:
        return None
    return members


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
    owner._native_fail = None
    owner._native_apply_host = None


def _apply_host_value_after_i64_overflow(owner: Any, value: Any) -> None:
    """i64 extract failed before native bound apply.

    OverflowError is a bridge signal, not a public validation miss.
    Fall through to host ``ValueValidator`` (Door A KEEP wording).
    """
    ValueValidator._validate_value(owner, None, value)


def _apply_host_value_after_f64_overflow(owner: Any, value: Any) -> None:
    """f64 extract failed before native bound apply.

    OverflowError is a bridge signal, not a public validation miss
    and not an L1 "overflow" message. Fall through to host
    ``ValueValidator`` (Door A KEEP wording).
    """
    ValueValidator._validate_value(owner, None, value)


def _apply_host_length_after_str_extract(owner: Any, value: Any) -> None:
    """UTF-8 extract failed before native length apply.

    OverflowError / UnicodeEncodeError is a bridge signal, not a public
    validation miss and not an L1 "overflow" message. Fall through to
    host ``LengthValidator`` (Door A KEEP wording, ``len(str)``).
    """
    LengthValidator._validate_length(owner, None, value)


def _apply_host_length_after_bytes_extract(owner: Any, value: Any) -> None:
    """bytes extract failed before native length apply.

    OverflowError / extract TypeError is a bridge signal, not a public
    validation miss and not an L1 "overflow" message. Fall through to
    host ``LengthValidator`` (Door A KEEP wording, ``len(bytes)``).
    """
    LengthValidator._validate_length(owner, None, value)


def _raise_native_bound_miss(owner: Any, fail: Any, value: Any) -> None:
    """Map peer ``FailKind`` to Door A KEEP wording. Unexpected kind is infra."""
    kinds = owner._native_fail
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
        case kinds.Member:
            _raise_host_integer_enum_type_miss(owner, value)
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


def _raise_host_integer_enum_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording for a closed IntegerEnum member-set plan.

    Same string as host ``TypeValidator``: the concrete annotation, then
    the value's type name. This raise is only the type door.
    ``validate()`` continues into the named extra when ``collect_all``
    is on. Not a native ``FailKind`` for plain ``int`` / ``str`` — those
    miss here before extract. ``FailKind.Member`` uses this same string.
    """
    annotation = owner.annotation
    raise TypeError(
        f"{owner.name} expect {annotation} type, "
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


def _bind_compiled_plan(owner: Any, peer: Any, compile_fn: Any, bounds: dict[str, Any]) -> None:
    try:
        owner._native_plan = compile_fn(**bounds)
        owner._native_fail = peer.FailKind
    except OverflowError:
        _clear_native(owner)
        return
    except Exception as err:
        _clear_native(owner)
        raise RuntimeError("ux_valio_native bind failed") from err


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No peer / unclosed path → ``_native_plan is None``."""
    int_bounds = _closed_integer_bounds(owner)
    if int_bounds is not None:
        peer = _load_native_peer()
        if peer is None:
            _clear_native(owner)
            return
        owner._native_apply = peer.apply
        owner._native_apply_host = apply_native_integer_bounds
        _bind_compiled_plan(owner, peer, peer.compile, int_bounds)
        return
    float_bounds = _closed_float_bounds(owner)
    if float_bounds is not None:
        peer = _load_native_peer()
        if peer is None:
            _clear_native(owner)
            return
        owner._native_apply = peer.apply_float
        owner._native_apply_host = apply_native_float_bounds
        _bind_compiled_plan(owner, peer, peer.compile_float, float_bounds)
        return
    str_bounds = _closed_string_length(owner)
    if str_bounds is not None:
        peer = _load_native_peer()
        if peer is None:
            _clear_native(owner)
            return
        owner._native_apply = peer.apply_string
        owner._native_apply_host = apply_native_string_length
        _bind_compiled_plan(owner, peer, peer.compile_string, str_bounds)
        return
    bytes_bounds = _closed_bytes_length(owner)
    if bytes_bounds is not None:
        peer = _load_native_peer()
        if peer is None:
            _clear_native(owner)
            return
        owner._native_apply = peer.apply_bytes
        owner._native_apply_host = apply_native_bytes_length
        _bind_compiled_plan(owner, peer, peer.compile_bytes, bytes_bounds)
        return
    members = _closed_integer_enum_members(owner)
    if members is None:
        _clear_native(owner)
        return
    peer = _load_native_peer()
    if peer is None:
        _clear_native(owner)
        return
    owner._native_apply = peer.apply_integer_enum
    owner._native_apply_host = apply_native_integer_enum
    _bind_compiled_plan(owner, peer, peer.compile_integer_enum, {"members": members})


def _apply_native_closed(
    owner: Any,
    value: Any,
    expected: type,
    raise_type_miss: Any,
    after_overflow: Any,
    extract_errors: type | tuple[type, ...] = OverflowError,
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
        _apply_host_value_after_i64_overflow,
    )


def apply_native_float_bounds(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. f64 extract miss stays on host.

    OverflowError at ``f64`` extract is a bridge signal (same three
    buckets as Integer: validation / bridge / peer-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A NaN/inf is IEEE compare, not a fourth
    bucket.
    """
    _apply_native_closed(
        owner,
        value,
        float,
        _raise_host_float_type_miss,
        _apply_host_value_after_f64_overflow,
    )


def apply_native_string_length(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. UTF-8 extract miss stays on host.

    OverflowError / UnicodeEncodeError at ``&str`` extract is a bridge
    signal (same three buckets as Integer/Float: validation / bridge /
    peer-infra ``RuntimeError`` naming ``ux_valio_native``). No public
    L1 "overflow" message. Door A length is ``len(str)`` codepoints.
    """
    _apply_native_closed(
        owner,
        value,
        str,
        _raise_host_string_type_miss,
        _apply_host_length_after_str_extract,
        (OverflowError, UnicodeError),
    )


def apply_native_bytes_length(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. bytes extract miss stays on host.

    OverflowError / extract TypeError at ``&[u8]`` extract is a bridge
    signal (same three buckets as Integer/Float/String: validation /
    bridge / peer-infra ``RuntimeError`` naming ``ux_valio_native``).
    No public L1 "overflow" message. Door A length is ``len(bytes)``.
    """
    _apply_native_closed(
        owner,
        value,
        bytes,
        _raise_host_bytes_type_miss,
        _apply_host_length_after_bytes_extract,
        (OverflowError, TypeError),
    )


def apply_native_integer_enum(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Out-of-i64 members stay on host.

    Closed IntegerEnum type door is host-first. A value that is not an
    ``IntEnum`` misses before extract (plain ``int`` / ``bool`` / ``str``
    / plain ``Enum``). An ``IntEnum`` is extracted as ``i64`` and checked
    against the compiled member set. A different enum with the same
    integer is in the set and still misses ``isinstance`` of the concrete
    annotation (KEEP). ``OverflowError`` at extract is a bridge signal
    (same three buckets: validation / bridge / peer-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Fall through to host ``TypeValidator``.
    """
    if value is None:
        return
    if not isinstance(value, enum.IntEnum):
        _raise_host_integer_enum_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except OverflowError:
        TypeValidator._validate_type(owner, None, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        if not isinstance(value, owner.annotation):
            _raise_host_integer_enum_type_miss(owner, value)
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_bounds(owner: Any, value: Any) -> None:
    """Dispatch the bind-time host apply. Unset bundle is a caller bug."""
    apply_host = getattr(owner, "_native_apply_host", None)
    if apply_host is None:
        raise RuntimeError("ux_valio_native apply failed")
    apply_host(owner, value)
