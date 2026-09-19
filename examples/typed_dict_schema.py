# SPDX-License-Identifier: MIT
"""TypedDict schema: builtin dict shape, Door A extras via Annotated."""

from dataclasses import dataclass
from typing import Annotated, TypedDict

from ux_valio import EmailValidator, StringValidator, Validator


class Person(TypedDict):
    name: Annotated[str, StringValidator(min_length=2)]
    email: Annotated[str, EmailValidator()]
    age: int


@dataclass
class Signup:
    person: Person = Validator()


def main() -> None:
    row = Signup(person={"name": "Ada", "email": "ada@example.com", "age": 36})
    print(row.person)


if __name__ == "__main__":
    main()
