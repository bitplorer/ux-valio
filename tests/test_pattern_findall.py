# SPDX-License-Identifier: MIT
"""PatternValidator uses findall substring match; Pattern ``&`` / ``|`` compose."""

from dataclasses import dataclass

import pytest

from ux_valio import (
    BytesValidator,
    Digit,
    NonDigit,
    NonWord,
    Pattern,
    PatternType,
    PatternValidator,
    Word,
    WordBoundary,
)


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


def test_digit_word_nondigit_nonword_are_pattern_types():
    assert Digit().pattern == r"\d"
    assert Word().pattern == r"\w"
    assert NonDigit().pattern == r"\D"
    assert NonWord().pattern == r"\W"
    assert isinstance(Digit(), PatternType)
    assert isinstance(Word(), PatternType)
    assert isinstance(NonDigit(), PatternType)
    assert isinstance(NonWord(), PatternType)


def test_digit_count_composes_on_existing_algebra():
    token = Pattern(r"A") & Digit(count=2)
    assert token.pattern == r"A\d{2}"

    @dataclass
    class Code:
        value: str = PatternValidator(pattern=token, debug=True)

    assert Code(value="A12").value == "A12"
    with pytest.raises(ValueError):
        Code(value="AB")


def test_word_findall_substring_keep():
    @dataclass
    class Token:
        value: str = PatternValidator(pattern=Word(count_min=1), debug=True)

    assert Token(value="a string").value == "a string"


def test_nondigit_nonword_compose_with_or():
    mixed = NonDigit() | NonWord()
    assert isinstance(mixed, PatternType)

    @dataclass
    class Punct:
        value: str = PatternValidator(pattern=mixed, debug=True)

    assert Punct(value="hello!").value == "hello!"
    with pytest.raises(ValueError):
        Punct(value="123")


def test_pattern_compose_none_fragment_is_type_error():
    with pytest.raises(TypeError):
        PatternType() & Digit()
    with pytest.raises(TypeError):
        Digit() | PatternType()
    with pytest.raises(TypeError):
        PatternType() & PatternType()


def test_pattern_compose_mixed_str_bytes_is_type_error():
    with pytest.raises(TypeError):
        Pattern(b"a") & Pattern("b")
    with pytest.raises(TypeError):
        Pattern("a") | Pattern(b"b")


def test_pattern_compose_same_kind_bytes_concatenates_as_bytes():
    combined = Pattern(b"a") & Pattern(b"b")
    assert combined.pattern == b"ab"
    alternated = Pattern(b"a") | Pattern(b"b")
    assert isinstance(alternated.pattern, bytes)
    assert b"a|b" in alternated.pattern


def test_inverted_count_min_max_is_value_error_at_construction():
    with pytest.raises(ValueError, match="count_max"):
        Pattern(r"a", count_min=5, count_max=2)
    with pytest.raises(ValueError, match="count_max"):
        Digit(count_min=5, count_max=2)


def test_pattern_bytes_keeps_bytes_identity():
    token = Pattern(b"ab")
    assert token.pattern == b"ab"
    counted = Pattern(b"a", count=2)
    assert counted.pattern == b"a{2}"


def test_pattern_validator_matches_bytes_against_bytes():
    @dataclass
    class Blob:
        b: bytes = BytesValidator(pattern=b"ab", debug=True)

    assert Blob(b=b"ab").b == b"ab"
    assert Blob(b=b"xxabxx").b == b"xxabxx"
    with pytest.raises(ValueError):
        Blob(b=b"cd")


def test_pattern_validator_mixed_str_bytes_is_type_error():
    @dataclass
    class Blob:
        b: bytes = BytesValidator(pattern="ab", debug=True)

    with pytest.raises(TypeError):
        Blob(b=b"ab")

    @dataclass
    class Text:
        s: str = PatternValidator(pattern=b"ab", debug=True)

    with pytest.raises(TypeError):
        Text(s="ab")
