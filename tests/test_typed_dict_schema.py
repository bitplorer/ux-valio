# SPDX-License-Identifier: MIT
"""TypedDict is the schema. No BaseModel / Schema twin. field-default hangs on keys."""

from dataclasses import dataclass
from typing import Annotated, TypedDict

import pytest

from ux_valio import EmailValidator, StringValidator, ValidationErrors, Validator


class Movie(TypedDict):
    title: str
    year: int


class Person(TypedDict):
    name: Annotated[str, StringValidator(min_length=2)]
    email: Annotated[str, EmailValidator()]
    age: int


@dataclass
class Catalog:
    movie: Movie = Validator()


@dataclass
class Signup:
    person: Person = Validator()


def test_typeddict_field_accepts_matching_mapping():
    assert Catalog(movie={"title": "Heat", "year": 1995}).movie["year"] == 1995


def test_typeddict_missing_required_key_is_type_error():
    with pytest.raises(TypeError):
        Catalog(movie={"title": "Heat"})


def test_typeddict_wrong_value_type_is_type_error():
    with pytest.raises(TypeError):
        Catalog(movie={"title": "Heat", "year": "1995"})


def test_typeddict_extra_key_is_rejected():
    with pytest.raises(TypeError):
        Catalog(movie={"title": "Heat", "year": 1995, "extra": 1})


def test_annotated_min_length_runs_on_typeddict_key():
    with pytest.raises(ValueError, match="person.name"):
        Signup(person={"name": "A", "email": "ada@example.com", "age": 30})


def test_annotated_email_runs_on_typeddict_key():
    with pytest.raises(ValueError, match="email"):
        Signup(person={"name": "Ada", "email": "not-an-email", "age": 30})


def test_annotated_typeddict_accepts_valid_person():
    got = Signup(
        person={"name": "Ada", "email": "ada@example.com", "age": 30}
    ).person
    assert got["email"] == "ada@example.com"


def test_notrequired_key_may_be_omitted():
    import sys

    if sys.version_info < (3, 11):
        pytest.skip("NotRequired is typing 3.11+")
    from typing import NotRequired

    class OptionalNick(TypedDict):
        name: str
        nick: NotRequired[str]

    @dataclass
    class Box:
        row: OptionalNick = Validator()

    assert OptionalNick.__required_keys__ == frozenset({"name"})
    assert OptionalNick.__optional_keys__ == frozenset({"nick"})
    assert "nick" not in Box(row={"name": "Ada"}).row
    assert Box(row={"name": "Ada", "nick": "A"}).row["nick"] == "A"
    with pytest.raises(TypeError):
        Box(row={"nick": "A"})
    with pytest.raises(TypeError):
        Box(row={"name": "Ada", "nick": 1})


def test_total_false_keys_are_all_optional():
    class Open(TypedDict, total=False):
        title: str
        year: int

    @dataclass
    class Box:
        row: Open = Validator()

    assert Open.__required_keys__ == frozenset()
    assert Box(row={}).row == {}
    assert Box(row={"title": "Heat"}).row["title"] == "Heat"
    with pytest.raises(TypeError):
        Box(row={"title": 1})
    with pytest.raises(TypeError):
        Box(row={"title": "Heat", "extra": 1})


def test_required_overrides_total_false():
    import sys

    if sys.version_info < (3, 11):
        pytest.skip("Required is typing 3.11+")
    from typing import Required

    class Patch(TypedDict, total=False):
        title: Required[str]
        year: int

    @dataclass
    class Box:
        row: Patch = Validator()

    assert Patch.__required_keys__ == frozenset({"title"})
    assert Patch.__optional_keys__ == frozenset({"year"})
    with pytest.raises(TypeError):
        Box(row={})
    with pytest.raises(TypeError):
        Box(row={"year": 1995})
    assert Box(row={"title": "Heat"}).row["title"] == "Heat"
    assert Box(row={"title": "Heat", "year": 1995}).row["year"] == 1995


def test_notrequired_annotated_skips_extras_when_omitted():
    import sys

    if sys.version_info < (3, 11):
        pytest.skip("NotRequired is typing 3.11+")
    from typing import NotRequired

    class Contact(TypedDict):
        name: str
        email: NotRequired[Annotated[str, EmailValidator()]]

    @dataclass
    class Box:
        row: Contact = Validator()

    assert Box(row={"name": "Ada"}).row == {"name": "Ada"}
    assert Box(row={"name": "Ada", "email": "ada@example.com"}).row["email"] == (
        "ada@example.com"
    )
    with pytest.raises(ValueError):
        Box(row={"name": "Ada", "email": "not-an-email"})


def test_annotated_notrequired_wrapping_is_the_same_door():
    import sys

    if sys.version_info < (3, 11):
        pytest.skip("NotRequired is typing 3.11+")
    from typing import NotRequired

    class Contact(TypedDict):
        name: str
        email: Annotated[NotRequired[str], EmailValidator()]

    @dataclass
    class Box:
        row: Contact = Validator()

    assert "email" not in Box(row={"name": "Ada"}).row
    with pytest.raises(ValueError):
        Box(row={"name": "Ada", "email": "not-an-email"})


def test_required_annotated_still_requires_the_key():
    import sys

    if sys.version_info < (3, 11):
        pytest.skip("Required is typing 3.11+")
    from typing import Required

    class Form(TypedDict, total=False):
        name: Required[Annotated[str, StringValidator(min_length=2)]]

    @dataclass
    class Box:
        row: Form = Validator()

    with pytest.raises(TypeError):
        Box(row={})
    with pytest.raises(ValueError, match="name"):
        Box(row={"name": "A"})
    assert Box(row={"name": "Ada"}).row["name"] == "Ada"


def test_typeddict_child_keeps_parent_required_keys():
    class Base(TypedDict):
        name: str

    class Child(Base, total=False):
        age: int

    @dataclass
    class Box:
        row: Child = Validator()

    with pytest.raises(TypeError):
        Box(row={})
    assert Box(row={"name": "Ada"}).row["name"] == "Ada"
    assert Box(row={"name": "Ada", "age": 1}).row["age"] == 1


def test_typeddict_pre_validate():
    class Profile(TypedDict):
        name: str = StringValidator()

        @name.pre_validate
        def strip_name(self, value):
            return value.strip()

    @dataclass
    class Box:
        person: Profile = Validator()

    built = Profile()
    assert not isinstance(built.get("name"), StringValidator)
    assert Box(person={"name": "  Ada  "}).person["name"] == "Ada"


def test_typeddict_validator():
    class Profile(TypedDict):
        name: str = StringValidator()

        @name.validator
        def no_digit(self, value):
            if any(char.isdigit() for char in value):
                raise ValueError("name must not contain digits")

    @dataclass
    class Box:
        person: Profile = Validator()

    assert Box(person={"name": "Ada"}).person["name"] == "Ada"
    with pytest.raises(ValueError, match="digits"):
        Box(person={"name": "Ada1"})
