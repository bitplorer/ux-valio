# SPDX-License-Identifier: MIT
"""Bound presence helpers. ``None`` is unset; ``0`` is specified."""

from __future__ import annotations

from typing import Any


def specified(*bounds: Any) -> bool:
    """True when every bound is present. None-only; ``0`` is specified."""
    return all(bound is not None for bound in bounds)


def reject_exclusive(left: Any, right: Any, message: str) -> None:
    if specified(left, right):
        raise ValueError(message)


def reject_inverted(lo: Any, hi: Any, message: str) -> None:
    if specified(lo, hi) and hi < lo:
        raise ValueError(message)


def bound(owner: Any, name: str) -> Any:
    value = getattr(owner, name, None)
    return value if value is not None else None
