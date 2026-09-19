# SPDX-License-Identifier: MIT
"""TypedDict is the schema. No BaseModel / Schema twin. Annotated hangs Door A."""

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

    assert "nick" not in Box(row={"name": "Ada"}).row
    assert Box(row={"name": "Ada", "nick": "A"}).row["nick"] == "A"


def test_collect_all_gathers_typeddict_key_extras():
    with pytest.raises((ValidationErrors, ValueError)):
        Signup(person={"name": "A", "email": "nope", "age": 30})
