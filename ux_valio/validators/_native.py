# SPDX-License-Identifier: MIT
"""Optional native apply peer. Not a taught import.

Bind-time choice: when ``ux_valio_native`` is importable and the specified
path is a closed Integer or Float bound plan (``int`` / ``float``
annotation + only ``ValueValidator`` bounds: min/max/gt/lt/eq), compile
a plan once. Type door is host-first ``isinstance`` then FFI extract
(``i64`` / ``f64``); bound units run after extract. Open TypeValidator /
Union / TypedDict / Annotated stay on the host. Missing or failed extra
→ host ``_active_units`` path. No import on the hot path after that
choice. Not Cap Door B.
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
    if fail == kinds.GreaterThan:
        gt = owner.gt
        raise ValueError(
            f"{owner.name} expect a value greater than {gt}, got {value} instead"
        )
    if fail == kinds.LessThan:
        lt = owner.lt
        raise ValueError(
            f"{owner.name} expect a value less than {lt}, got {value} instead"
        )
    if fail == kinds.Equal:
        of_value = owner.value
        raise ValueError(
            f"{owner.name} expect the value {of_value}, got {value} as value instead"
        )
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
    _raise_host_closed_type_miss(owner, value)


def _raise_host_float_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording. Closed Float type door is host-first.

    FFI type is the later ``f64`` extract. Python ``int`` / ``bool``
    are not ``float`` (KEEP). ``None`` is skipped by the caller.
    ``collect_all`` continues into host ``ValueValidator``. NaN / ±inf
    are ``float`` and reach apply.
    """
    _raise_host_closed_type_miss(owner, value)


def _raise_host_closed_type_miss(owner: Any, value: Any) -> None:
    """KEEP TypeError wording for a closed Integer or Float plan."""
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
    if float_bounds is None:
        _clear_native(owner)
        return
    peer = _load_native_peer()
    if peer is None:
        _clear_native(owner)
        return
    owner._native_apply = peer.apply_float
    owner._native_apply_host = apply_native_float_bounds
    _bind_compiled_plan(owner, peer, peer.compile_float, float_bounds)


def _apply_native_closed(
    owner: Any,
    value: Any,
    expected: type,
    raise_type_miss: Any,
    after_overflow: Any,
) -> None:
    """One FFI apply. Host formats KEEP wording. Extract overflow stays on host."""
    if value is None:
        return
    if not isinstance(value, expected):
        raise_type_miss(owner, value)
        return
    try:
        fail = owner._native_apply(owner._native_plan, value)
    except OverflowError:
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


def apply_native_bounds(owner: Any, value: Any) -> None:
    """Dispatch the bind-time host apply. Unset bundle is a caller bug."""
    apply_host = getattr(owner, "_native_apply_host", None)
    if apply_host is None:
        raise RuntimeError("ux_valio_native apply failed")
    apply_host(owner, value)
