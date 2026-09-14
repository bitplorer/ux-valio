# SPDX-License-Identifier: MIT
"""PatternValidator uses findall substring match; Pattern ``&`` / ``|`` compose."""

from dataclasses import dataclass

import pytest

from ux_valio import Pattern, PatternValidator, PatternType, WordBoundary


WORD_1_OR_MORE = r"\w+"


def test_empty_pattern_accepts_any_string():
    @dataclass
    class PatternEmpty:
        value: str = PatternValidator(debug=True)

    assert PatternEmpty(value="1").value == "1"


def test_findall_none_is_skipped():
    @dataclass
    class Patterned:
        value: str = PatternValidator(pattern=WORD_1_OR_MORE, debug=True)

    assert Patterned(value=None).value is None


def test_findall_empty_string_fails_when_debug():
    @dataclass
    class Patterned:
        value: str = PatternValidator(pattern=WORD_1_OR_MORE, debug=True)

    with pytest.raises(ValueError):
        Patterned(value="")


def test_findall_empty_string_swallowed_when_debug_falsy():
    @dataclass
    class Patterned:
        value: str = PatternValidator(pattern=WORD_1_OR_MORE, debug=False)

    assert Patterned(value="").value is None


def test_findall_substring_match_a_string():
    @dataclass
    class Patterned:
        value: str = PatternValidator(pattern=WORD_1_OR_MORE, debug=True)

    assert Patterned(value="a string").value == "a string"


def test_pattern_and_combinator_concatenates():
    digits = Pattern(r"\d", count=2, alias="dd")
    composed = Pattern(r"A") & digits
    assert isinstance(composed, PatternType)
    assert composed.pattern == r"A\d{2}"

    @dataclass
    class Token:
        value: str = PatternValidator(pattern=composed, debug=True)

    assert Token(value="A12").value == "A12"
    with pytest.raises(ValueError):
        Token(value="AB")


def test_pattern_or_combinator_alternates():
    composed = Pattern(r"cat") | Pattern(r"dog")
    assert "cat|dog" in composed.pattern

    @dataclass
    class Pet:
        value: str = PatternValidator(pattern=composed, debug=True)

    assert Pet(value="a cat here").value == "a cat here"
    assert Pet(value="doggo").value == "doggo"
    with pytest.raises(ValueError):
        Pet(value="bird")


def test_word_boundary_is_a_pattern_type():
    bounded = WordBoundary() & Pattern(r"hi") & WordBoundary()
    assert isinstance(bounded, PatternType)

    @dataclass
    class Greet:
        value: str = PatternValidator(pattern=bounded, debug=True)

    assert Greet(value="say hi now").value == "say hi now"


def test_and_or_require_pattern_type():
    with pytest.raises(TypeError):
        Pattern(r"a") & "b"
    with pytest.raises(TypeError):
        Pattern(r"a") | "b"
