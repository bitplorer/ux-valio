# SPDX-License-Identifier: MIT
"""Stdlib ``re`` atoms and ``^`` / ``$`` anchors on the Pattern algebra.

``WordBoundary`` stays an atom ``\\b`` (valio wrap-``WordBoundary`` is KEEP).
``StartsWith`` / ``EndsWith`` match valio@3415c03 ``regexer/regexps.py``.
"""

from __future__ import annotations

from ux_valio.pattern._algebra import (
    Pattern,
    PatternType,
    prefix_fragment,
    require_pattern_type,
    suffix_fragment,
)


class WordBoundary(PatternType):
    def __init__(self, alias: str | None = None) -> None:
        super().__init__(r"\b", alias=alias or r"\b")


class _StdlibAtom(PatternType):
    """Quantified stdlib ``re`` atom on the existing Pattern algebra."""

    token: str

    def __init__(
        self,
        count: int | None = None,
        count_min: int | None = None,
        count_max: int | None = None,
        greedy: bool = True,
        alias: str | None = None,
    ) -> None:
        super().__init__(
            Pattern(
                self.token,
                count=count,
                count_min=count_min,
                count_max=count_max,
                greedy=greedy,
                alias=alias,
            )
        )


class Digit(_StdlibAtom):
    token = r"\d"


class Word(_StdlibAtom):
    token = r"\w"


class NonDigit(_StdlibAtom):
    token = r"\D"


class NonWord(_StdlibAtom):
    token = r"\W"


class WhiteSpace(_StdlibAtom):
    token = r"\s"


class NonWhiteSpace(_StdlibAtom):
    token = r"\S"


class StartsWith(PatternType):
    """``^fragment`` — valio ``regexer/regexps.py`` ``StartsWith`` L414."""

    def __init__(self, pattern: PatternType, alias: str | None = None) -> None:
        source = require_pattern_type(pattern)
        super().__init__(
            prefix_fragment("^", source.pattern),
            alias=alias if alias is not None else source.alias,
        )


class EndsWith(PatternType):
    """``fragment$`` — valio ``regexer/regexps.py`` ``EndsWith`` L421."""

    def __init__(self, pattern: PatternType, alias: str | None = None) -> None:
        source = require_pattern_type(pattern)
        super().__init__(
            suffix_fragment(source.pattern, "$"),
            alias=alias if alias is not None else source.alias,
        )
