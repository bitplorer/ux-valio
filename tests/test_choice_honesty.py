# SPDX-License-Identifier: MIT
"""Choice bags skip None. not_in_choice must not TypeError on a string bag."""

from dataclasses import dataclass

import pytest

from ux_valio import ChoiceValidator, Validator


def test_in_choice_skips_none():
    v = ChoiceValidator(in_choice=["a", "b"], debug=True)
    v.validate(None, None)

    @dataclass
    class Box:
        s: str = Validator(in_choice=["a", "b"], debug=True)

    assert Box(s=None).s is None
    assert Box(s="a").s == "a"
    with pytest.raises(ValueError):
        Box(s="c")


def test_not_in_choice_skips_none():
    v = ChoiceValidator(not_in_choice=["taken"], debug=True)
    v.validate(None, None)
    v.validate(None, "ok")
    with pytest.raises(ValueError, match="does not expect"):
        v.validate(None, "taken")


def test_not_in_choice_string_bag_does_not_typeerror_on_none():
    """``None in "abc"`` is TypeError; optional None must skip like in_choice."""
    v = ChoiceValidator(not_in_choice="abc", debug=True)
    v.validate(None, None)

    @dataclass
    class Box:
        s: str = Validator(not_in_choice="xyz", debug=True)

    assert Box(s=None).s is None
    with pytest.raises(ValueError):
        Box(s="x")
