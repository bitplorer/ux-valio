# SPDX-License-Identifier: MIT
"""Closed-plan detectors for the optional native peer.

Each function returns compile kwargs only when the specified path is
one ``Plan`` variant. Integer / Float own ``BoundUnit`` values.
String / Bytes own ``LengthUnit`` values. IntegerEnum / StringEnum
own a member set. Boolean / Decimal are type-door markers. There is
no shared unit bag. An unclosed path returns ``None`` and stays on
the host. This module does not import facades and does not apply.
Not Cap Door B. Date* stays HOLD.
"""

from __future__ import annotations

import decimal
import enum
import types
from typing import Any, Union, get_args, get_origin

from ux_valio.validators.leaves import TypeValidator
from ux_valio.validators.length import LengthValidator
from ux_valio.validators.value import ValueValidator

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
