# SPDX-License-Identifier: MIT
"""Validator objects compose with each other as one Door A descriptor.

Inheritance hygiene (facades do not subclass leaves) is a separate lock.
"""

from dataclasses import dataclass

import pytest

from ux_valio import (
    AllOf,
    AnyOf,
    Chain,
    IntegerValidator,
    LengthValidator,
    PatternValidator,
    RequiredValidator,
    StringValidator,
    ValidateProperty,
    Validator,
)


def test_length_and_required_as_one_field_default():
    field = LengthValidator(min_length=3, debug=True) & RequiredValidator(required=True)
    assert isinstance(field, AllOf)
    assert isinstance(field, ValidateProperty)

    @dataclass
    class User:
        name: str = field

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError, match="minimum length"):
        User(name="Ab")
    with pytest.raises(ValueError, match="requires value"):
        User(name=None)


def test_allof_length_required_explicit():
    field = AllOf(
        LengthValidator(min_length=3, debug=True),
        RequiredValidator(required=True),
    )

    @dataclass
    class User:
        name: str = field

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError):
        User(name="Ab")
    with pytest.raises(ValueError):
        User(name=None)


def test_chain_is_ordered_allof():
    assert Chain is AllOf
    field = Chain(
        LengthValidator(min_length=2, debug=True),
        RequiredValidator(required=True),
    )
    assert isinstance(field, AllOf)
    assert type(field) is AllOf

    @dataclass
    class Token:
        s: str = field

    assert Token(s="ok").s == "ok"
    with pytest.raises(ValueError):
        Token(s="x")


def test_and_flattens_nested_allof():
    composed = (
        LengthValidator(min_length=1, debug=True)
        & RequiredValidator(required=True)
        & LengthValidator(max_length=5, debug=True)
    )
    assert type(composed) is AllOf
    assert len(composed.validators) == 3


def test_anyof_pattern_alternatives():
    field = PatternValidator(pattern=r"cat", debug=True) | PatternValidator(pattern=r"dog")
    assert isinstance(field, AnyOf)

    @dataclass
    class Pet:
        value: str = field

    assert Pet(value="a cat here").value == "a cat here"
    assert Pet(value="doggo").value == "doggo"
    with pytest.raises(ValueError, match="none of the alternatives"):
        Pet(value="bird")


def test_compose_facade_with_leaf():
    field = StringValidator(debug=True, max_length=8) & RequiredValidator(required=True)

    @dataclass
    class User:
        name: str = field

    assert User(name="Ada").name == "Ada"
    with pytest.raises(ValueError):
        User(name="abcdefghijk")
    with pytest.raises(ValueError):
        User(name=None)


def test_integer_and_multiple_still_one_descriptor():
    field = IntegerValidator(debug=True, min_value=0) & RequiredValidator(required=True)

    @dataclass
    class Count:
        n: int = field

    assert Count(n=2).n == 2
    with pytest.raises(ValueError):
        Count(n=-1)


def test_compose_does_not_multiple_inherit_leaves():
    field = LengthValidator(min_length=1) & RequiredValidator(required=True)
    assert not issubclass(type(field), LengthValidator)
    assert not issubclass(type(field), RequiredValidator)
    assert type(field).__bases__[0].__name__ != "LengthValidator"
    assert issubclass(type(field), ValidateProperty)
    assert not issubclass(Validator, AllOf)


def test_conflicting_typed_facades_fail_at_compose():
    with pytest.raises(TypeError, match="conflicting annotations"):
        IntegerValidator(debug=True) & StringValidator(debug=True)


def test_allof_and_requires_validators():
    with pytest.raises(TypeError):
        LengthValidator(min_length=1) & "nope"
    with pytest.raises(TypeError):
        AllOf(LengthValidator(min_length=1))


def test_anyof_typed_facades_do_not_conflict_and_alternatives_match():
    field = IntegerValidator(debug=True) | StringValidator(debug=True)
    assert isinstance(field, AnyOf)
    assert field.annotation is None

    class Box:
        x = field

    box = Box()
    box.x = 1
    assert box.x == 1
    box.x = "a"
    assert box.x == "a"


def test_anyof_integer_or_untyped_accepts_str():
    field = IntegerValidator(debug=True) | Validator(debug=True)

    class Box:
        x = field

    box = Box()
    box.x = "a"
    assert box.x == "a"
    box.x = 2
    assert box.x == 2


def test_anyof_union_owner_binds_without_and_gate():
    field = IntegerValidator(debug=True) | StringValidator(debug=True)

    @dataclass
    class Either:
        n: int | str = field

    assert Either(n=1).n == 1
    assert Either(n="a").n == "a"
    with pytest.raises(ValueError, match="none of the alternatives"):
        Either(n=1.5)


def test_allof_conflicting_typed_facades_still_typeerror():
    with pytest.raises(TypeError, match="conflicting annotations"):
        AllOf(IntegerValidator(debug=True), StringValidator(debug=True))


def test_compose_types_are_bound_once_on_package_import():
    """``&`` / ``|`` must not import compose on each operator use."""
    import inspect

    from ux_valio.validators import base as base_mod
    from ux_valio.validators.compose import AllOf, AnyOf

    assert base_mod._AllOf is AllOf
    assert base_mod._AnyOf is AnyOf
    first = base_mod._load_compose_types()
    second = base_mod._load_compose_types()
    assert first is second
    assert first[0] is AllOf
    assert first[1] is AnyOf
    and_src = inspect.getsource(ValidateProperty.__and__)
    or_src = inspect.getsource(ValidateProperty.__or__)
    assert "from ux_valio.validators.compose import" not in and_src
    assert "from ux_valio.validators.compose import" not in or_src
    left = IntegerValidator(debug=True, min_value=0)
    right = RequiredValidator(required=True)
    assert type(left & right) is AllOf
    assert type(left | StringValidator(debug=True)) is AnyOf
    assert base_mod._AllOf is AllOf


def test_allof_post_validate_cannot_store_member_facade_lie():
    from ux_valio import EmailValidator, LengthValidator
    from ux_valio.validators.hooks import _bag_key

    field = EmailValidator(debug=True) & LengthValidator(min_length=3, debug=True)

    def smash(instance, value):
        return "not-an-email"

    @dataclass
    class Contact:
        s: str = field

    field.add_post_validator(smash, namespace=_bag_key(Contact))
    with pytest.raises(ValueError, match="email"):
        Contact(s="ada@example.com")


def test_allof_post_validate_may_shorten_unnamed_length_member():
    """AllOf path bounds are not re-run. Named extra of a StringValidator is no-op."""
    from ux_valio.validators.hooks import _bag_key

    field = StringValidator(min_length=3, debug=True) & RequiredValidator(required=True)

    def shorten(instance, value):
        return "x"

    @dataclass
    class Tag:
        s: str = field

    field.add_post_validator(shorten, namespace=_bag_key(Tag))
    assert Tag(s="abcd").s == "x"


def test_anyof_post_validate_must_still_match_one_alternative():
    from ux_valio import EmailValidator, PaymentCardValidator
    from ux_valio.validators.hooks import _bag_key

    field = EmailValidator(debug=True) | PaymentCardValidator(debug=True)

    def smash(instance, value):
        return "not-an-email"

    @dataclass
    class Either:
        s: str = field

    field.add_post_validator(smash, namespace=_bag_key(Either))
    with pytest.raises(ValueError, match="none of the alternatives"):
        Either(s="ada@example.com")


def test_anyof_post_validate_may_store_when_string_alternative_holds():
    from ux_valio import EmailValidator
    from ux_valio.validators.hooks import _bag_key

    field = EmailValidator(debug=True) | StringValidator(debug=True)

    def smash(instance, value):
        return "not-an-email"

    @dataclass
    class Either:
        s: str = field

    field.add_post_validator(smash, namespace=_bag_key(Either))
    assert Either(s="ada@example.com").s == "not-an-email"
