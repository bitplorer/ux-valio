# SPDX-License-Identifier: MIT
"""Bind door for the optional native peer. Not a taught import.

Private split of the same walk (not a second door):

- ``_native_closed`` — ``_closed_*`` detectors
- ``_native_apply`` — ``apply_native_*`` family helpers, the
  ``FailKind`` map, and extract bridges
- this module — ``_load_native_peer``, ``_select_*``,
  ``bind_native_plan``, and ``apply_native_bounds``

``Plan`` is one variant per family. Integer / Float own
``BoundUnit`` values. String / Bytes own ``LengthUnit`` values.
IntegerEnum / StringEnum own a member set. Boolean / Decimal are
type-door markers. There is no shared unit bag.

Bind-time choice: when ``ux_valio_native`` is importable and the
specified path is one closed family, compile that variant once.
Type door is host-first ``isinstance`` then FFI extract (``i64`` /
``f64`` / ``&str`` / ``&[u8]`` / ``bool`` / ``decimal.Decimal``);
bound / length / member checks run after extract. StringEnum
extract is the member's ``.value`` as UTF-8 ``&str``. Boolean
extract is exact ``bool`` (``1`` / ``0`` are not coerced). Decimal
extract is exact ``decimal.Decimal`` (``float`` / ``int`` /
``bool`` are not coerced; string coerce stays host
``_pre_validate``). No scale unit. Open TypeValidator / Union /
TypedDict / Annotated / pattern / plain ``EnumValidator`` / Date*
stay on the host. A ``BooleanValidator`` or ``DecimalValidator``
with any extra unit stays on the host. Missing or failed extra →
host ``_active_units`` path. No import on the hot path after that
choice. Each family keeps its own ``compile_*`` / ``apply_*`` pair.
Not Cap Door B.
"""

from __future__ import annotations

from typing import Any

from ux_valio.validators._native_apply import (
    _bind_compiled_plan,
    _clear_native,
    apply_native_boolean,
    apply_native_bytes_length,
    apply_native_decimal,
    apply_native_float_bounds,
    apply_native_integer_bounds,
    apply_native_integer_enum,
    apply_native_string_enum,
    apply_native_string_length,
)
from ux_valio.validators._native_closed import (
    _closed_boolean,
    _closed_bytes_length,
    _closed_decimal,
    _closed_float_bounds,
    _closed_integer_bounds,
    _closed_integer_enum_members,
    _closed_string_enum_members,
    _closed_string_length,
)

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


def apply_native_bounds(owner: Any, value: Any) -> None:
    """Dispatch the bind-time host apply. Unset bundle is a caller bug."""
    apply_host = getattr(owner, "_native_apply_host", None)
    if apply_host is None:
        raise RuntimeError("ux_valio_native apply failed")
    apply_host(owner, value)


type _ClosedPair = tuple[Any, Any, Any, dict[str, Any]]


def _select_integer_bounds(peer: Any, bounds: dict[str, int]) -> _ClosedPair:
    """Closed Integer: ``compile_integer`` and ``apply_integer`` stay a pair."""
    return peer.apply_integer, apply_native_integer_bounds, peer.compile_integer, bounds


def _select_float_bounds(peer: Any, bounds: dict[str, float]) -> _ClosedPair:
    """Closed Float: ``compile_float`` and ``apply_float`` stay a pair."""
    return peer.apply_float, apply_native_float_bounds, peer.compile_float, bounds


def _select_string_length(peer: Any, bounds: dict[str, int]) -> _ClosedPair:
    """Closed String: ``compile_string`` and ``apply_string`` stay a pair."""
    return peer.apply_string, apply_native_string_length, peer.compile_string, bounds


def _select_bytes_length(peer: Any, bounds: dict[str, int]) -> _ClosedPair:
    """Closed Bytes: ``compile_bytes`` and ``apply_bytes`` stay a pair."""
    return peer.apply_bytes, apply_native_bytes_length, peer.compile_bytes, bounds


def _select_integer_enum(peer: Any, members: list[int]) -> _ClosedPair:
    """Closed IntegerEnum: ``compile_integer_enum`` / ``apply_integer_enum`` stay a pair."""
    return (
        peer.apply_integer_enum,
        apply_native_integer_enum,
        peer.compile_integer_enum,
        {"members": members},
    )


def _select_boolean(peer: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed Boolean: ``compile_boolean`` and ``apply_boolean`` stay a pair."""
    return peer.apply_boolean, apply_native_boolean, peer.compile_boolean, bounds


def _select_decimal(peer: Any, bounds: dict[str, Any]) -> _ClosedPair:
    """Closed Decimal: ``compile_decimal`` and ``apply_decimal`` stay a pair."""
    return peer.apply_decimal, apply_native_decimal, peer.compile_decimal, bounds


def _select_string_enum(peer: Any, members: list[str]) -> _ClosedPair:
    """Closed StringEnum: ``compile_string_enum`` / ``apply_string_enum`` stay a pair."""
    return (
        peer.apply_string_enum,
        apply_native_string_enum,
        peer.compile_string_enum,
        {"members": members},
    )


def bind_native_plan(owner: Any) -> None:
    """Compile at bind. No peer / unclosed path → ``_native_plan is None``.

    One walk. Each closed family keeps its own ``compile_*`` / ``apply_*``
    pair: Integer / Float own ``BoundUnit`` values, String / Bytes own
    ``LengthUnit`` values, IntegerEnum / StringEnum own a member set,
    Boolean / Decimal are type-door markers. An unclosed path does not
    import the extra. Do not merge a pair into one door.
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
    )
    for detect, select in families:
        payload = detect(owner)
        if payload is None:
            continue
        peer = _load_native_peer()
        if peer is None:
            _clear_native(owner)
            return
        apply, host_apply, compile_fn, kwargs = select(peer, payload)
        owner._native_apply = apply
        owner._native_apply_host = host_apply
        _bind_compiled_plan(owner, peer, compile_fn, kwargs)
        return
    _clear_native(owner)
