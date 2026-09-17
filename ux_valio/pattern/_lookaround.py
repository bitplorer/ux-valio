# SPDX-License-Identifier: MIT
"""Thin stdlib lookaround PatternTypes.

valio@3415c03 ``valio/regexer/regexps.py``:
``IfPrecededBy`` L449, ``IfNotPrecededBy`` L456, ``IfFollowedBy`` L463,
``IfNotFollowedBy`` L470. Not the CapturingGroup / IfGroupNameMatched stack.
"""

from __future__ import annotations

from ux_valio.pattern._algebra import PatternType, require_pattern_type, wrap_fragment


class IfPrecededBy(PatternType):
    """``(?<=fragment)`` — valio ``regexer/regexps.py`` L449."""

    def __init__(self, pattern: PatternType, alias: str | None = None) -> None:
        source = require_pattern_type(pattern)
        super().__init__(
            wrap_fragment("(?<=", source.pattern, ")"),
            alias=alias if alias is not None else source.alias,
        )


class IfNotPrecededBy(PatternType):
    """``(?<!fragment)`` — valio ``regexer/regexps.py`` L456."""

    def __init__(self, pattern: PatternType, alias: str | None = None) -> None:
        source = require_pattern_type(pattern)
        super().__init__(
            wrap_fragment("(?<!", source.pattern, ")"),
            alias=alias if alias is not None else source.alias,
        )


class IfFollowedBy(PatternType):
    """``(?=fragment)`` — valio ``regexer/regexps.py`` L463."""

    def __init__(self, pattern: PatternType, alias: str | None = None) -> None:
        source = require_pattern_type(pattern)
        super().__init__(
            wrap_fragment("(?=", source.pattern, ")"),
            alias=alias if alias is not None else source.alias,
        )


class IfNotFollowedBy(PatternType):
    """``(?!fragment)`` — valio ``regexer/regexps.py`` L470."""

    def __init__(self, pattern: PatternType, alias: str | None = None) -> None:
        source = require_pattern_type(pattern)
        super().__init__(
            wrap_fragment("(?!", source.pattern, ")"),
            alias=alias if alias is not None else source.alias,
        )
