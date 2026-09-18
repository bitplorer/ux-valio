# SPDX-License-Identifier: MIT
"""Pattern algebra: fragments, ``&`` / ``|``, quantifiers.

Internal module. Taught import is ``ux_valio`` / ``ux_valio.pattern``.
"""

from __future__ import annotations

from typing import Union

PatternSource = Union[str, bytes, "PatternType"]


class PatternType:
    """Regex fragment with ``&`` / ``|`` composition."""

    pattern: str | bytes | None
    raw_pattern: str | bytes | None
    quantifier: str
    alias: str

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


def require_pattern_type(value: object) -> PatternType:
    """Fail-closed PatternType with a present fragment."""
    if not isinstance(value, PatternType):
        raise TypeError(
            f"expected PatternType type, got {type(value).__name__} instead"
        )
    if value.pattern is None:
        raise TypeError("pattern fragment is missing")
    return value


def _join_fragments(left: object, right: object, joiner: str = "") -> str | bytes:
    """Concatenate same-kind str or bytes fragments. Missing or mixed is TypeError."""
    if left is None or right is None:
        raise TypeError("pattern fragment is missing")
    if isinstance(left, bytes) and isinstance(right, bytes):
        mid = joiner.encode("ascii") if joiner else b""
        return left + mid + right
    if isinstance(left, str) and isinstance(right, str):
        return f"{left}{joiner}{right}"
    raise TypeError(
        "pattern fragments must be the same str or bytes kind, "
        f"got {type(left).__name__} and {type(right).__name__}"
    )


def _wrap_alternation(combined: str | bytes) -> str | bytes:
    if isinstance(combined, bytes):
        return b"(?:" + combined + b")"
    return f"(?:{combined})"


def _attach_quantifier(pattern: str | bytes, quantifier: str) -> str | bytes:
    if not quantifier:
        return pattern
    if isinstance(pattern, bytes):
        return pattern + quantifier.encode("ascii")
    return f"{pattern}{quantifier}"


def prefix_fragment(token: str, fragment: str | bytes | None) -> str | bytes:

    """Prefix an ascii regex token onto a same-kind fragment."""
    if fragment is None:
        raise TypeError("pattern fragment is missing")
    if isinstance(fragment, bytes):
        return token.encode("ascii") + fragment
    if isinstance(fragment, str):
        return f"{token}{fragment}"
    raise TypeError(
        "pattern fragment must be str or bytes, "
        f"got {type(fragment).__name__}"
    )


def suffix_fragment(fragment: str | bytes | None, token: str) -> str | bytes:

    """Suffix an ascii regex token onto a same-kind fragment."""
    if fragment is None:
        raise TypeError("pattern fragment is missing")
    if isinstance(fragment, bytes):
        return fragment + token.encode("ascii")
    if isinstance(fragment, str):
        return f"{fragment}{token}"
    raise TypeError(
        "pattern fragment must be str or bytes, "
        f"got {type(fragment).__name__}"
    )


def wrap_fragment(
    open_token: str, fragment: str | bytes | None, close_token: str
) -> str | bytes:

    """Wrap a fragment with ascii open/close tokens. Bytes stay bytes."""
    return suffix_fragment(prefix_fragment(open_token, fragment), close_token)


class AndPattern(PatternType):
    def __init__(self, first: PatternType, second: PatternType) -> None:
        self.pattern = _join_fragments(first.pattern, second.pattern)
        self.raw_pattern = self.pattern
        self.quantifier = ""
        self.alias = "".join(filter(None, [first.alias, second.alias]))


class OrPattern(PatternType):
    def __init__(self, first: PatternType, second: PatternType) -> None:
        combined = _join_fragments(first.pattern, second.pattern, "|")
        self.pattern = _wrap_alternation(combined)
        self.raw_pattern = combined
        self.quantifier = ""
        self.alias = " or ".join(filter(None, [first.alias, second.alias]))


def quantifier_token(
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
    if count_min is not None and count_max is not None and count_max < count_min:
        raise ValueError("count_max can not be less than count_min")
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
        self.quantifier = quantifier or quantifier_token(
            count, count_min, count_max, greedy
        )
        self.raw_pattern = raw_pattern if raw_pattern is not None else pattern
        self.pattern = _attach_quantifier(pattern, self.quantifier)
        self.alias = alias or ""
