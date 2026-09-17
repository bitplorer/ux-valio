# SPDX-License-Identifier: MIT
"""Character-class ``SetOf`` on the Pattern algebra.

Thin ``[fragment]`` / ``[^fragment]`` shape from valio@3415c03
``valio/regexer/regexps.py`` ``SetOf`` L261. Not the regexer ``allow_set``
SyntaxError, not Escape-as-invert, not a second regexer package.
"""

from __future__ import annotations

from ux_valio.pattern._algebra import (
    PatternType,
    _attach_quantifier,
    prefix_fragment,
    quantifier_token,
    require_pattern_type,
    wrap_fragment,
)


def _char_class(inner: str | bytes, negated: bool, quantifier: str) -> str | bytes:
    body = prefix_fragment("^", inner) if negated else inner
    return _attach_quantifier(wrap_fragment("[", body, "]"), quantifier)


class SetOf(PatternType):
    """``[raw]`` character class. ``~SetOf(...)`` is the negated class."""

    def __init__(
        self,
        pattern: PatternType,
        count: int | None = None,
        count_min: int | None = None,
        count_max: int | None = None,
        greedy: bool = True,
        alias: str | None = None,
        *,
        _negated: bool = False,
    ) -> None:
        source = require_pattern_type(pattern)
        inner = source.raw_pattern if source.raw_pattern is not None else source.pattern
        if inner is None:
            raise TypeError("pattern fragment is missing")
        set_quantifier = quantifier_token(count, count_min, count_max, greedy)
        existing = source.quantifier or ""
        if set_quantifier and existing:
            raise ValueError(
                f"pattern quantifiers {existing} already exist, "
                "SetOf quantifiers can't be set"
            )
        self.quantifier = set_quantifier if not existing else existing
        self.raw_pattern = inner
        self.set_negated = bool(_negated)
        self.pattern = _char_class(inner, self.set_negated, self.quantifier)
        self.alias = alias if alias is not None else source.alias

    def __invert__(self) -> "SetOf":
        inner = self.raw_pattern
        if not isinstance(inner, (str, bytes)):
            raise TypeError("pattern fragment is missing")
        flipped = SetOf.__new__(SetOf)
        flipped.raw_pattern = inner
        flipped.quantifier = self.quantifier
        flipped.set_negated = not self.set_negated
        flipped.alias = self.alias
        flipped.pattern = _char_class(inner, flipped.set_negated, flipped.quantifier)
        return flipped
