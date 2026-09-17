# SPDX-License-Identifier: MIT
"""Pattern combinators.

``PatternType`` supports ``&`` (concatenate) and ``|`` (alternation).
``PatternValidator`` matches with ``re.findall`` (substring), not fullmatch.
Stdlib atoms ``Digit`` / ``Word`` / ``NonDigit`` / ``NonWord`` /
``WhiteSpace`` / ``NonWhiteSpace`` share the count-kwargs door.
``WordBoundary`` stays an atom ``\\b``.
Thin valio@3415c03 PatternTypes on this algebra: ``StartsWith`` / ``EndsWith``
(``regexer/regexps.py`` L414 / L421), lookarounds ``IfPrecededBy`` /
``IfNotPrecededBy`` / ``IfFollowedBy`` / ``IfNotFollowedBy`` (L449–L470),
and ``SetOf`` character-class shape (L261).

Taught import is the package root: ``from ux_valio import Pattern, SetOf``.
``from ux_valio.pattern import Pattern`` is the same objects (package re-home,
not a second door). ``Contained`` / ``IfContained`` are KEEP-absent — they
do not exist in valio@3415c03. CapturingGroup / WordGroups / scanString /
pyparsing / ``ux_valio.regexer`` stay KEEP-absent.
"""

from ux_valio.pattern._algebra import Pattern, PatternType
from ux_valio.pattern._atoms import (
    Digit,
    EndsWith,
    NonDigit,
    NonWhiteSpace,
    NonWord,
    StartsWith,
    WhiteSpace,
    Word,
    WordBoundary,
)
from ux_valio.pattern._lookaround import (
    IfFollowedBy,
    IfNotFollowedBy,
    IfNotPrecededBy,
    IfPrecededBy,
)
from ux_valio.pattern._sets import SetOf

__all__ = [
    "Digit",
    "EndsWith",
    "IfFollowedBy",
    "IfNotFollowedBy",
    "IfNotPrecededBy",
    "IfPrecededBy",
    "NonDigit",
    "NonWhiteSpace",
    "NonWord",
    "Pattern",
    "PatternType",
    "SetOf",
    "StartsWith",
    "WhiteSpace",
    "Word",
    "WordBoundary",
]
