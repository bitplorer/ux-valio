# SPDX-License-Identifier: MIT
"""Pattern combinators.

``PatternType`` supports ``&`` (concatenate) and ``|`` (alternation).
``PatternValidator`` matches with ``re.findall`` (substring), not fullmatch.
``Digit`` / ``Word`` / ``NonDigit`` / ``NonWord`` are stdlib ``re`` atoms
on this algebra. ``WordBoundary`` stays an atom ``\\b``.
"""

from __future__ import annotations

from typing import Union

PatternSource = Union[str, bytes, "PatternType"]


class PatternType:
    """Regex fragment with ``&`` / ``|`` composition."""

    def __init__(
        self,
        pattern: PatternSource | None = None,
        alias: str | None = None,
    ) -> None:
        if isinstance(pattern, PatternType):
            self.pattern = pattern.pattern
            self.raw_pattern = pattern.raw_pattern
            self.quantifier = pattern.quantifier
            self.alias = alias if alias is not None else pattern.alias
        elif isinstance(pattern, (str, bytes)):
            self.pattern = pattern
            self.raw_pattern = pattern
            self.quantifier = ""
            self.alias = alias or ""
        else:
            self.pattern = None
            self.raw_pattern = None
            self.quantifier = ""
            self.alias = alias or ""

    def __and__(self, other: object) -> "AndPattern":
        if not isinstance(other, PatternType):
            raise TypeError(
                f"expected {type(self).__name__} type, got {type(other).__name__} instead"
            )
        return AndPattern(self, other)

    def __or__(self, other: object) -> "OrPattern":
        if not isinstance(other, PatternType):
            raise TypeError(
                f"expected {type(self).__name__} type, got {type(other).__name__} instead"
            )
        return OrPattern(self, other)

    def __str__(self) -> str:
        return str(self.pattern)


class AndPattern(PatternType):
    def __init__(self, first: PatternType, second: PatternType) -> None:
        self.pattern = f"{first.pattern}{second.pattern}"
        self.raw_pattern = self.pattern
        self.quantifier = ""
        self.alias = "".join(filter(None, [first.alias, second.alias]))


class OrPattern(PatternType):
    def __init__(self, first: PatternType, second: PatternType) -> None:
        combined = f"{first.pattern}|{second.pattern}"
        self.pattern = f"(?:{combined})"
        self.raw_pattern = combined
        self.quantifier = ""
        self.alias = " or ".join(filter(None, [first.alias, second.alias]))


def _quantifier(
    count: int | None,
    count_min: int | None,
    count_max: int | None,
    greedy: bool,
) -> str:
    if count is not None and (count_min is not None or count_max is not None):
        raise ValueError(
            "count and count_min or count and count_max values can not be used together"
        )
    if count is not None:
        count_min = count_max = count
    if count_min is None and count_max is None:
        return ""
    if count_min is not None and count_min < 0:
        raise ValueError(
            f"expect count_min to be equal to or greater than 0, got {count_min} instead"
        )
    lo = 0 if count_min is None else count_min
    if count_min is not None and count_max is not None and count_min == count_max:
        token = f"{{{count_min}}}"
    elif count_max is None:
        token = f"{{{lo},}}"
    else:
        token = f"{{{lo},{count_max}}}"
    shortcuts = {"{0,}": "*", "{1,}": "+", "{0,1}": "?"}
    rendered = shortcuts.get(token, token)
    if not greedy:
        rendered += "?"
    return rendered


class Pattern(PatternType):
    def __init__(
        self,
        pattern: str | bytes,
        raw_pattern: str | bytes | None = None,
        quantifier: str | None = None,
        count: int | None = None,
        count_min: int | None = None,
        count_max: int | None = None,
        greedy: bool = True,
        alias: str | None = None,
    ) -> None:
        self.quantifier = quantifier or _quantifier(count, count_min, count_max, greedy)
        self.raw_pattern = raw_pattern if raw_pattern is not None else pattern
        self.pattern = f"{pattern}{self.quantifier}"
        self.alias = alias or ""


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
