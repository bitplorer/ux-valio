# SPDX-License-Identifier: MIT
"""Fail-closed annotation conflict at descriptor assignment.

valio@3415c03 ``valio/descriptor/descriptors.py`` ``_may_set_or_ensure_annotation_match``
(L157–202) raises when both sides are set and do not match. Owner wins only
when ``validator.annotation`` was None. Validator annotation is kept when the
owner has none.

Reuse with a matching annotation and a different field name raises
``AttributeError`` (same file ``_set_name`` L134–155). Dual-schema
``Union[T, Validator]`` / typingx is HOLD — not invented here.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Union

import pytest

from ux_valio import BooleanValidator, IntegerValidator, Property, StringValidator, Validator
from ux_valio.descriptor import Property as DescriptorProperty


def test_integer_validator_on_str_field_raises_at_class_body():
    field = IntegerValidator(debug=True)
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Bad:
            n: str = field
    assert field.errors
    assert isinstance(field.errors[-1], TypeError)


def test_string_validator_on_int_field_raises_at_class_body():
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Bad:
            n: int = StringValidator(debug=True)


def test_conflict_raises_even_when_debug_is_falsy():
    field = IntegerValidator(debug=False)
    with pytest.raises(TypeError, match="annotation did not match"):
        @dataclass
        class Bad:
            n: str = field
    assert field.errors


def test_matching_int_annotation_does_not_overwrite_and_validates():
    field = IntegerValidator(debug=True)

    @dataclass
    class Count:
        n: int = field

    assert field.annotation is int
    assert Count(n=0).n == 0
    with pytest.raises(TypeError):
        Count(n="nope")


def test_owner_wins_only_when_validator_annotation_was_none():
    field = Validator(debug=True)

    @dataclass
    class User:
        name: str = field

    assert field.annotation is str
    assert User(name="Ada").name == "Ada"
    with pytest.raises(TypeError):
        User(name=1)


def test_validator_annotation_kept_when_owner_has_none():
    field = IntegerValidator(debug=True)

    class Box:
        n = field

    assert field.annotation is int
    box = Box()
    box.n = 2
    assert box.n == 2
    with pytest.raises(TypeError):
        box.n = "nope"


def test_boolean_vs_int_is_a_conflict_not_quiet_owner_win():
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Flag:
            n: int = BooleanValidator(debug=True)


def test_optional_int_conflicts_with_integer_validator():
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Maybe:
            n: int | None = IntegerValidator(debug=True)


def test_union_owner_conflicts_with_integer_validator():
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Either:
            n: int | str = IntegerValidator(debug=True)


def test_stdlib_union_forms_agree_when_validator_annotation_was_none():
    field = Validator(debug=True)
    field.annotation = Optional[int]

    @dataclass
    class Maybe:
        n: int | None = field

    assert field.annotation is Optional[int]
    assert Maybe(n=1).n == 1
    assert Maybe(n=None).n is None
    with pytest.raises(TypeError):
        Maybe(n="nope")


def test_typing_union_and_pep604_union_agree_without_typing_extensions():
    field = Validator(debug=True)
    field.annotation = Union[int, str]

    @dataclass
    class Either:
        n: int | str = field

    assert field.annotation is Union[int, str]
    assert Either(n=1).n == 1
    assert Either(n="a").n == "a"
    with pytest.raises(TypeError):
        Either(n=1.5)


def test_reused_validator_same_annotation_different_name_raises():
    shared = Validator(debug=True)
    with pytest.raises(AttributeError, match="did not match"):
        @dataclass
        class Two:
            a: str = shared
            b: str = shared


def test_reused_integer_validator_across_classes_raises():
    shared = IntegerValidator(debug=True)

    @dataclass
    class First:
        n: int = shared

    with pytest.raises(AttributeError, match="attribute names did not match"):
        @dataclass
        class Second:
            m: int = shared


def test_property_conflict_message_names_owner_and_descriptor():
    field = IntegerValidator(debug=True)
    with pytest.raises(TypeError, match=r"Bad.n: str annotation did not match"):
        @dataclass
        class Bad:
            n: str = field
    with pytest.raises(TypeError, match="IntegerValidator"):
        @dataclass
        class Also:
            n: str = IntegerValidator(debug=True)


def test_list_int_agrees_with_typing_list_int():
    field = Validator(debug=True)
    field.annotation = List[int]

    @dataclass
    class Box:
        items: list[int] = field

    assert field.annotation is List[int]
    assert Box(items=[1]).items == [1]


def test_dict_and_set_typing_aliases_agree_with_builtins():
    dfield = Validator(debug=True)
    dfield.annotation = Dict[str, int]
    sfield = Validator(debug=True)
    sfield.annotation = Set[int]

    @dataclass
    class Pair:
        m: dict[str, int] = dfield
        items: set[int] = sfield

    assert Pair(m={"a": 1}, items={1}).m == {"a": 1}


def test_bare_list_still_conflicts_with_list_int():
    field = Validator(debug=True)
    field.annotation = list
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Box:
            items: list[int] = field


def test_descriptor_property_owner_none_keeps_unset_annotation():
    field = DescriptorProperty()
    assert field.annotation is None

    class Bare:
        x = field

    assert field.annotation is None
    assert isinstance(field, Property)
