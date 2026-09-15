# SPDX-License-Identifier: MIT
"""Ordered unique validation concerns. Double-call / nested leaf fail closed.

``value`` already owns min/max/eq. ``length`` already owns min/max.
A second ``validate()`` is a new pass — per-pass uniqueness, not process lifetime.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from ux_valio.validators.errors import continue_or_raise, raise_collected

Lookup = Callable[[Any, Any, Any], Any]

_PATH_OWNED_LEAVES = {
    "value": frozenset({"min_value", "max_value", "eq"}),
    "length": frozenset({"min_length", "max_length"}),
}

DEFAULT_PATH_NAMES = (
    "reassignment",
    "type",
    "required",
    "pattern",
    "multiple_of",
    "length",
    "value",
    "choice",
)


class ValidationPath:
    """Ordered unique validation concerns. Double-call / nested leaf fail closed."""

    def __init__(self, names: Iterable[str]) -> None:
        names = tuple(names)
        seen: set[str] = set()
        for name in names:
            if name in seen:
                raise ValueError(f"validation path double-call: {name!r}")
            seen.add(name)
        for aggregate, owned in _PATH_OWNED_LEAVES.items():
            clash = seen & owned
            if aggregate in seen and clash:
                raise ValueError(
                    f"validation path conflict: {aggregate!r} already owns {sorted(clash)}"
                )
        self.names = names

    def run(
        self,
        owner: Any,
        instance: Any,
        value: Any,
        lookup: dict[str, Lookup],
        collect_all: bool = False,
    ) -> list[Any]:
        ran: set[str] = set()
        results = []
        errors: list[BaseException] = []
        for name in self.names:
            if name in ran:
                raise ValueError(f"validation path double-call: {name!r}")
            ran.add(name)
            try:
                results.append(lookup[name](owner, instance, value))
            except Exception as err:
                continue_or_raise(collect_all, errors, err)
                results.append(None)
        raise_collected(errors, name=getattr(owner, "name", None))
        return results
