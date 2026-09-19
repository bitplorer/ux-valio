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
from ux_valio.descriptor import _annotations_agree


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


def test_descriptor_class_annotation_peels_to_store_type():
    """Type checkers want ``name: StringValidator = StringValidator()``.

    Runtime peels the facade class to its store type (``str``) so it
    agrees with ``StringValidator.annotation``.
    """

    @dataclass
    class User:
        name: StringValidator = StringValidator(debug=True)

        @name.add_process_pre_validate
        def strip(self, value: str) -> str:
            return value.strip()

    user = User(name=" ada ")
    assert user.name == "ada"
    assert User.name.annotation is str


def test_validator_subscript_annotation_peels_to_store_type():
    @dataclass
    class User:
        name: Validator[str] = StringValidator(debug=True)

    assert User(name="ada").name == "ada"


def test_integer_validator_class_annotation_on_string_field_still_conflicts():
    with pytest.raises(TypeError, match="did not match"):
        @dataclass
        class Bad:
            n: IntegerValidator = StringValidator(debug=True)


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


def test_coercing_facade_agrees_with_str_or_stored_owner():
    from uuid import UUID

    from ux_valio import UUIDValidator

    @dataclass
    class AsUuid:
        u: UUID = UUIDValidator(debug=True)

    @dataclass
    class AsStr:
        u: str = UUIDValidator(debug=True)

    @dataclass
    class AsUnion:
        u: UUID | str = UUIDValidator(debug=True)

    assert AsUuid.__dict__["u"].annotation == UUID | str
    assert AsStr.__dict__["u"].annotation == UUID | str
    assert AsUnion.__dict__["u"].annotation == UUID | str


def test_stdlib_union_forms_agree_when_validator_annotation_was_none():
    field = Validator(debug=True)
    field.annotation = Optional[int]

    @dataclass
    class Maybe:
        n: int | None = field

    assert _annotations_agree(field.annotation, Optional[int])
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

    # 3.14: Union[int, str] is types.UnionType; `is` is not interned.
    assert _annotations_agree(field.annotation, Union[int, str])
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


def test_postponed_validator_does_not_copy_string_into_type_door():
    ns: dict = {}
    exec(
        """
from __future__ import annotations
from dataclasses import dataclass
from ux_valio import Validator
import pytest

field = Validator(debug=True)
with pytest.raises(TypeError, match=r\"N.n: 'int'\"):
    @dataclass
    class N:
        n: int = field
assert field.annotation is None
assert not isinstance(field.annotation, str)
""",
        ns,
    )


def test_forwardref_owner_annotation_is_not_copied_or_evaled():
    from typing import ForwardRef

    field = Validator(debug=True)

    class Holder:
        pass

    Holder.__annotations__ = {"n": ForwardRef("int")}
    with pytest.raises(TypeError, match="unresolved"):
        field.__set_name__(Holder, "n")
    assert field.annotation is None
    assert field.annotation is not int
