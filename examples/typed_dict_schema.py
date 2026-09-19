# SPDX-License-Identifier: MIT
"""TypedDict schema: field-default assignment + Annotated extras. No BaseModel."""

from dataclasses import dataclass
from typing import Annotated, TypedDict

from ux_valio import EmailValidator, StringValidator, Validator


class Person(TypedDict):
    name: str = StringValidator(min_length=2)
    email: Annotated[str, EmailValidator()]
    age: int

    @name.pre_validate
    def strip_name(self, value: str) -> str:
        return value.strip()

    @name.validator
    def no_digit(self, value: str) -> None:
        if any(char.isdigit() for char in value):
            raise ValueError("name must not contain digits")


@dataclass
class Signup:
    person: Person = Validator()


def main() -> None:
    row = Signup(person={"name": "  Ada  ", "email": "ada@example.com", "age": 36})
    print(row.person)


if __name__ == "__main__":
    main()
