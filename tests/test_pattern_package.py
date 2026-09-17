# SPDX-License-Identifier: MIT
"""Pattern package re-home plus thin valio@3415c03 PatternTypes."""

from dataclasses import dataclass
from pathlib import Path

import pytest

import ux_valio
from ux_valio import (
    Digit,
    EndsWith,
    IfFollowedBy,
    IfNotFollowedBy,
    IfNotPrecededBy,
    IfPrecededBy,
    Pattern,
    PatternType,
    PatternValidator,
    SetOf,
    StartsWith,
    WordBoundary,
)
from ux_valio.pattern import (
    Digit as PkgDigit,
    Pattern as PkgPattern,
    SetOf as PkgSetOf,
    StartsWith as PkgStartsWith,
)

ROOT = Path(__file__).resolve().parents[1]


def test_pattern_module_is_a_package_not_a_file():
    assert not (ROOT / "ux_valio" / "pattern.py").exists()
    assert (ROOT / "ux_valio" / "pattern" / "__init__.py").is_file()


def test_root_and_pattern_package_reexport_the_same_objects():
    assert ux_valio.Pattern is PkgPattern
    assert ux_valio.Digit is PkgDigit
    assert ux_valio.SetOf is PkgSetOf
    assert ux_valio.StartsWith is PkgStartsWith
    assert Pattern is PkgPattern


def test_contained_ifcontained_are_keep_absent():
    for name in ("Contained", "IfContained", "NotContained", "IfNotContained"):
        assert name not in ux_valio.__all__
        assert not hasattr(ux_valio, name)
        assert name not in ux_valio.pattern.__all__
        assert not hasattr(ux_valio.pattern, name)


def test_capturing_group_stack_and_regexer_stay_absent():
    assert not (ROOT / "ux_valio" / "regexer").exists()
    for name in (
        "CapturingGroup",
        "NonCapturingGroup",
        "NamedCapturingGroup",
        "WordGroups",
        "DigitGroups",
        "IfGroupNameMatched",
        "scanString",
        "StartOfString",
        "EndOfString",
        "Escape",
    ):
        assert name not in ux_valio.__all__
        assert not hasattr(ux_valio, name)


def test_starts_with_and_ends_with_compose():
    token = StartsWith(Pattern(r"INV-")) & Digit(count=4) & EndsWith(Pattern(r"Z"))
    assert token.pattern == r"^INV-\d{4}Z$"

    @dataclass
    class Sku:
        code: str = PatternValidator(pattern=token, debug=True)

    assert Sku(code="INV-0099Z").code == "INV-0099Z"
    with pytest.raises(ValueError):
        Sku(code="xINV-0099Z")
    with pytest.raises(ValueError):
        Sku(code="INV-0099")


def test_starts_with_requires_pattern_type():
    with pytest.raises(TypeError):
        StartsWith("INV-")
    with pytest.raises(TypeError):
        EndsWith("Z")
    with pytest.raises(TypeError):
        StartsWith(PatternType())


def test_starts_with_bytes_keeps_bytes_identity():
    bounded = StartsWith(Pattern(b"AB")) & EndsWith(Pattern(b"Z"))
    assert bounded.pattern == b"^ABZ$"


def test_set_of_is_a_character_class():
    hex_digit = SetOf(Pattern(r"0-9a-f"), count=2)
    assert hex_digit.pattern == r"[0-9a-f]{2}"
    negated = ~SetOf(Pattern(r"0-9"))
    assert negated.pattern == r"[^0-9]"
    assert (~~SetOf(Pattern(r"0-9"))).pattern == r"[0-9]"

    @dataclass
    class Pair:
        value: str = PatternValidator(pattern=hex_digit, debug=True)

    assert Pair(value="ab").value == "ab"
    with pytest.raises(ValueError):
        Pair(value="zz")


def test_set_of_rejects_double_quantifier():
    with pytest.raises(ValueError, match="quantifiers"):
        SetOf(Digit(count=2), count=3)


def test_set_of_requires_pattern_type():
    with pytest.raises(TypeError):
        SetOf("0-9")
    with pytest.raises(TypeError):
        SetOf(PatternType())


def test_set_of_bytes_keeps_bytes_identity():
    klass = SetOf(Pattern(b"ab"))
    assert klass.pattern == b"[ab]"
    assert (~klass).pattern == b"[^ab]"


def test_lookaround_zero_width_compose():
    amount = Digit(count_min=1) & IfFollowedBy(Pattern(r"kg"))
    assert amount.pattern == r"\d+(?=kg)"

    @dataclass
    class Mass:
        text: str = PatternValidator(pattern=amount, debug=True)

    assert Mass(text="12kg").text == "12kg"
    with pytest.raises(ValueError):
        Mass(text="12lb")


def test_if_preceded_by_and_not_variants():
    currency = IfPrecededBy(Pattern(r"USD")) & Digit(count_min=1)
    assert currency.pattern == r"(?<=USD)\d+"
    assert IfNotPrecededBy(Pattern(r"USD")).pattern == r"(?<!USD)"
    assert IfNotFollowedBy(Pattern(r"kg")).pattern == r"(?!kg)"

    @dataclass
    class Money:
        text: str = PatternValidator(pattern=currency, debug=True)

    assert Money(text="USD40").text == "USD40"
    with pytest.raises(ValueError):
        Money(text="EUR40")


def test_lookaround_requires_pattern_type():
    with pytest.raises(TypeError):
        IfPrecededBy("USD")
    with pytest.raises(TypeError):
        IfFollowedBy(PatternType())


def test_lookaround_bytes_keeps_bytes_identity():
    assert IfPrecededBy(Pattern(b"USD")).pattern == b"(?<=USD)"
    assert IfFollowedBy(Pattern(b"kg")).pattern == b"(?=kg)"


def test_pattern_package_all_is_reexported_from_root():
    leaked = set(ux_valio.pattern.__all__) - set(ux_valio.__all__)
    assert leaked == set()


def test_word_boundary_stays_an_atom():
    assert WordBoundary().pattern == r"\b"
    bounded = WordBoundary() & Pattern(r"hi") & WordBoundary()
    assert isinstance(bounded, PatternType)
