# SPDX-License-Identifier: MIT
"""Optional native apply peer. Not a taught import.

Bind-time choice: when ``ux_valio_native`` is importable and the specified
path is a closed Integer bound plan (``int`` annotation + only
``ValueValidator`` bounds: min/max/gt/lt/eq), compile a plan once.
Each set extracts an ``i64`` and makes one FFI ``apply``. Missing or
failed extra → host ``_active_units`` path. No import on the hot path
after that choice. Not Cap Door B.
"""

from __future__ import annotations

from typing import Any

from ux_valio.errors import raise_collected
from ux_valio.validators.leaves import TypeValidator
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


def _closed_integer_bounds(owner: Any) -> dict[str, int] | None:
    """Compile kwargs when the specified path is Integer + ValueValidator bounds."""
    if getattr(owner, "annotation", None) is not int:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (
        TypeValidator._validate_type,
        ValueValidator._validate_value,
    ):
        return None
    bounds: dict[str, int] = {}
    for host_name, compile_name in _HOST_BOUND_TO_COMPILE:
        raw = getattr(owner, host_name, None)
        if raw is None:
            continue
        if type(raw) is not int:
            return None
        bounds[compile_name] = raw
    if not bounds:
        return None
    return bounds


def _clear_native(owner: Any) -> None:
    """One host-fallback clear for the bind-time native bundle."""
    owner._native_plan = None
    owner._native_apply = None
    owner._native_fail = None


def _apply_host_value_after_i64_overflow(owner: Any, value: Any) -> None:
    """i64 extract failed before native bound apply.

    OverflowError is a bridge signal, not a public validation miss.
    Fall through to host ``ValueValidator`` (Door A KEEP wording).
    """
    ValueValidator._validate_value(owner, None, value)


def _raise_native_bound_miss(owner: Any, fail: Any, value: Any) -> None:
    """Map peer ``FailKind`` to Door A KEEP wording. Unexpected kind is infra."""
    kinds = owner._native_fail
    if fail == kinds.MinValue:
        min_value = owner.min_value
        raise ValueError(
            f"{owner.name} expect the minimum value of {min_value}, "
            f"got {value} instead"
        )
    if fail == kinds.MaxValue:
        max_value = owner.max_value
        raise ValueError(
            f"{owner.name} expect the maximum value of {max_value}, "
            f"got {value} instead"
        )
    if fail == kinds.Gt:
        gt = owner.gt
        raise ValueError(
            f"{owner.name} expect a value greater than {gt}, got {value} instead"
        )
    if fail == kinds.Lt:
        lt = owner.lt
        raise ValueError(
            f"{owner.name} expect a value less than {lt}, got {value} instead"
        )
    if fail == kinds.Eq:
        of_value = owner.value
        raise ValueError(
            f"{owner.name} expect the value {of_value}, got {value} as value instead"
        )
    raise RuntimeError(
        f"ux_valio_native apply returned unexpected fail kind {fail!r}"
    )


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No peer / unclosed path → ``_native_plan is None``."""
    bounds = _closed_integer_bounds(owner)
    if bounds is None:
        _clear_native(owner)
        return
    peer = _load_native_peer()
    if peer is None:
        _clear_native(owner)
        return
    try:
        owner._native_plan = peer.compile(**bounds)
        owner._native_apply = peer.apply
        owner._native_fail = peer.FailKind
    except OverflowError:
        _clear_native(owner)
    except Exception as err:
        _clear_native(owner)
        raise RuntimeError("ux_valio_native bind failed") from err


def apply_native_integer_bounds(owner: Any, value: Any) -> None:
    """One FFI apply. Host formats KEEP wording. Out-of-i64 ints stay on host."""
    if value is None:
        return
    if not isinstance(value, int):
        err = TypeError(
            f"{owner.name} expect {owner.annotation} type, "
            f"got {type(value).__name__} type instead"
        )
        if not owner.collect_all:
            raise err
        errors: list[BaseException] = [err]
        try:
            ValueValidator._validate_value(owner, None, value)
        except Exception as second:
            errors.append(second)
        raise_collected(errors, name=owner.name)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except OverflowError:
        _apply_host_value_after_i64_overflow(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    _raise_native_bound_miss(owner, fail, value)
