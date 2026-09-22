# SPDX-License-Identifier: MIT
"""Host apply for one compiled ``Plan`` variant.

One FFI ``apply_*`` per set. ``FailKind`` maps to KEEP wording.
Extract miss is a bridge back to the host unit, not a public
overflow message. Integer / Float walk ``BoundUnit``. String /
Bytes walk ``LengthUnit``. IntegerEnum / StringEnum walk their
member set. Boolean / Decimal are type-door markers (no bound
unit, no scale unit). Not Cap Door B. Date* stays HOLD.
"""

from __future__ import annotations

import decimal
from typing import Any

from ux_valio.errors import raise_collected
from ux_valio.validators.leaves import TypeValidator
from ux_valio.validators.length import LengthValidator
from ux_valio.validators.value import ValueValidator


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


def _apply_host_string_enum_after_str_extract(owner: Any, value: Any) -> None:
    """UTF-8 extract failed before native member-set apply.

    OverflowError / UnicodeError is a bridge signal, not a public
    validation miss and not an L1 "overflow" message. Fall through to
    host ``TypeValidator`` (Door A KEEP wording). A member whose value
    is not UTF-8 never compiled (bind stays on the host).
    """
    TypeValidator._validate_type(owner, None, value)


def _apply_host_integer_enum_after_i64_overflow(owner: Any, value: Any) -> None:
    """i64 extract failed before native member-set apply.

    OverflowError is a bridge signal, not a public validation miss and
    not an L1 "overflow" message. Fall through to host
    ``TypeValidator`` (Door A KEEP wording). A member whose value does
    not fit i64 never compiled (bind stays on the host).
    """
    TypeValidator._validate_type(owner, None, value)


def _apply_host_decimal_after_extract(owner: Any, value: Any) -> None:
    """Decimal extract failed before native type-door apply.

    Extract TypeError is a bridge signal, not a public validation miss
    and not an L1 "overflow" message. Fall through to host
    ``TypeValidator`` (Door A KEEP wording). ``float`` / ``int`` /
    ``bool`` miss ``isinstance`` before extract (no float bridge). A
    raw ``str`` is coerced in host ``_pre_validate`` before apply.
    """
    TypeValidator._validate_type(owner, None, value)


def _apply_host_boolean_after_extract(owner: Any, value: Any) -> None:
    """bool extract failed before native type-door apply.

    Extract TypeError is a bridge signal, not a public validation miss
    and not an L1 "overflow" message. Fall through to host
    ``TypeValidator`` (Door A KEEP wording). ``1`` / ``0`` miss
    ``isinstance`` before extract (no coerce).
    """
    TypeValidator._validate_type(owner, None, value)


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
        case kinds.NotMember:
            raise TypeError(
                f"{owner.name} expect {owner.annotation} type, "
                f"got {type(value).__name__} type instead"
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
    """KEEP TypeError wording for a closed IntegerEnum or StringEnum plan."""
    raise TypeError(
        f"{owner.name} expect {owner.annotation} type, "
        f"got {type(value).__name__} type instead"
    )


def _raise_host_string_enum_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed StringEnum type door is host-first.

    FFI type is the later ``&str`` extract of ``value.value``. The
    concrete enum on the field is the member class, so a plain ``str``
    (including one equal to a member value), ``bytes``, ``int``,
    ``bool``, or another enum misses here. ``None`` is skipped by the
    caller. ``collect_all`` continues into the named str-Enum extra
    from ``validate``, not inside this raise.
    """
    _raise_host_enum_type_miss(owner, value)


def _raise_host_integer_enum_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed IntegerEnum type door is host-first.

    FFI type is the later ``i64`` extract. The concrete ``enum.IntEnum``
    on the field is the member class, so a plain ``int``, ``bool``,
    ``str``, or another enum misses here — including another
    ``IntEnum`` whose integer collides with a member value. ``None`` is
    skipped by the caller. ``collect_all`` continues into the named
    ``enum.IntEnum`` extra from ``validate``, not inside this raise.
    """
    _raise_host_enum_type_miss(owner, value)


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


def apply_native_string_enum(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-UTF-8 stays on host.

    The FFI argument is ``value.value`` (UTF-8 ``&str``), not the enum
    object. OverflowError / UnicodeError at ``&str`` extract is a
    bridge signal (same three buckets as String length: validation
    ``FailKind`` / bridge / peer-infra ``RuntimeError`` naming
    ``ux_valio_native``). No public L1 "overflow" message. Door A
    membership is the concrete enum class first, then exact UTF-8
    equality with the compiled member values.
    """
    if value is None:
        return
    if not isinstance(value, owner.annotation):
        _raise_host_string_enum_type_miss(owner, value)
        return
    raw = value.value
    if type(raw) is not str:
        _apply_host_string_enum_after_str_extract(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, raw)
    except (OverflowError, UnicodeError):
        _apply_host_string_enum_after_str_extract(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_integer_enum(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Out-of-i64 ints stay on host.

    OverflowError at ``i64`` extract is a bridge signal (same three
    buckets as Integer: validation ``FailKind`` / bridge / peer-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A membership is the concrete enum class
    first, then exact ``i64`` equality with the compiled member values.
    """
    _apply_native_closed(
        owner,
        value,
        owner.annotation,
        _raise_host_integer_enum_type_miss,
        _apply_host_integer_enum_after_i64_overflow,
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


def apply_native_decimal(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-Decimal stays on host.

    TypeError at ``decimal.Decimal`` extract is a bridge signal (same
    three buckets as Boolean: validation ``FailKind`` / bridge /
    peer-infra ``RuntimeError`` naming ``ux_valio_native``). No public
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
        _apply_host_decimal_after_extract(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)


def apply_native_boolean(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Non-bool stays on host.

    TypeError at ``bool`` extract is a bridge signal (same three
    buckets as Integer: validation ``FailKind`` / bridge / peer-infra
    ``RuntimeError`` naming ``ux_valio_native``). No public L1
    "overflow" message. Door A is exact ``bool``: ``True`` and
    ``False`` pass; ``1`` and ``0`` do not coerce. No bound unit.
    """
    _apply_native_closed(
        owner,
        value,
        bool,
        _raise_host_boolean_type_miss,
        _apply_host_boolean_after_extract,
        TypeError,
    )
