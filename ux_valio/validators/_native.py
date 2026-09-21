# SPDX-License-Identifier: MIT
"""Optional native apply peer. Not a taught import.

Bind-time choice: when ``ux_valio_native`` is importable and the specified
path is closed ``Integer`` + ``MinValue(i64)``, compile a plan once.
Each set extracts an ``i64`` and makes one FFI ``apply``. Missing or
failed extra → host ``_active_units`` path. No import on the hot path
after that choice. Not Cap Door B.
"""

from __future__ import annotations

from typing import Any

from ux_valio.errors import raise_collected
from ux_valio.validators.leaves import TypeValidator
from ux_valio.validators.value import ValueValidator

_I64_BITS = 63

_peer: Any | None = None
_probed = False


def _load_native_peer() -> Any | None:
    """Import the extra once. Failed install is host apply, not a hot-path error."""
    global _peer, _probed
    if _probed:
        return _peer
    _probed = True
    try:
        import ux_valio_native as peer
    except Exception:
        _peer = None
        return None
    _peer = peer
    return _peer


def _closed_integer_min_value(owner: Any) -> int | None:
    """Return ``min_value`` when the specified path is Integer + MinValue(i64)."""
    if getattr(owner, "annotation", None) is not int:
        return None
    units = getattr(owner, "_active_units", None)
    if units != (
        TypeValidator._validate_type,
        ValueValidator._validate_value,
    ):
        return None
    if any(
        getattr(owner, name, None) is not None
        for name in ("gt", "value", "max_value", "lt")
    ):
        return None
    min_value = getattr(owner, "min_value", None)
    if type(min_value) is not int:
        return None
    if min_value.bit_length() > _I64_BITS:
        return None
    return min_value


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No peer / unclosed path → ``_native_plan is None``."""
    min_value = _closed_integer_min_value(owner)
    if min_value is None:
        owner._native_plan = None
        owner._native_apply = None
        owner._native_fail_min = None
        owner._native_fail_type = None
        return
    peer = _load_native_peer()
    if peer is None:
        owner._native_plan = None
        owner._native_apply = None
        owner._native_fail_min = None
        owner._native_fail_type = None
        return
    try:
        owner._native_plan = peer.compile(min_value)
        owner._native_apply = peer.apply
        owner._native_fail_min = peer.FailKind.MinValue
        owner._native_fail_type = peer.FailKind.NotInteger
    except Exception:
        owner._native_plan = None
        owner._native_apply = None
        owner._native_fail_min = None
        owner._native_fail_type = None


def apply_native_integer_min_value(owner: Any, value: Any) -> None:
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
    if value.bit_length() > _I64_BITS:
        ValueValidator._validate_value(owner, None, value)
        return
    fail = owner._native_apply(owner._native_plan, value)
    if fail is None:
        return
    if fail == owner._native_fail_min:
        min_value = owner.min_value
        raise ValueError(
            f"{owner.name} expect the minimum value of {min_value}, "
            f"got {value} instead"
        )
    if fail == owner._native_fail_type:
        raise TypeError(
            f"{owner.name} expect {owner.annotation} type, "
            f"got {type(value).__name__} type instead"
        )
    raise TypeError(f"{owner.name} native apply failed")
