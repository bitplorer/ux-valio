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

_peer: Any | None = None
_probed = False


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


def _closed_integer_min_value(owner: Any) -> int | None:
    """Return ``min_value`` when the specified path is Integer + MinValue."""
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
    return min_value


def _clear_native(owner: Any) -> None:
    """One host-fallback clear for the bind-time native bundle."""
    owner._native_plan = None
    owner._native_apply = None
    owner._native_fail_min = None


def _apply_host_value_after_i64_overflow(owner: Any, value: Any) -> None:
    """i64 extract failed before native MinValue.

    OverflowError is a bridge signal, not a public validation miss.
    Fall through to host ``ValueValidator`` (Door A KEEP wording).
    """
    ValueValidator._validate_value(owner, None, value)


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No peer / unclosed path → ``_native_plan is None``."""
    min_value = _closed_integer_min_value(owner)
    if min_value is None:
        _clear_native(owner)
        return
    peer = _load_native_peer()
    if peer is None:
        _clear_native(owner)
        return
    try:
        owner._native_plan = peer.compile(min_value)
        owner._native_apply = peer.apply
        owner._native_fail_min = peer.FailKind.MinValue
    except OverflowError:
        _clear_native(owner)
    except Exception as err:
        _clear_native(owner)
        raise RuntimeError("ux_valio_native bind failed") from err


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
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except OverflowError:
        _apply_host_value_after_i64_overflow(owner, value)
        return
    except Exception as err:
        raise RuntimeError("ux_valio_native apply failed") from err
    if fail is None:
        return
    if fail == owner._native_fail_min:
        min_value = owner.min_value
        raise ValueError(
            f"{owner.name} expect the minimum value of {min_value}, "
            f"got {value} instead"
        )
    raise RuntimeError(
        f"ux_valio_native apply returned unexpected fail kind {fail!r}"
    )
