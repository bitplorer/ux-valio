# SPDX-License-Identifier: MIT
"""TypedDict schema: field-default assignment + Annotated extras. No BaseModel."""

from dataclasses import dataclass
from typing import Annotated, TypedDict

from ux_valio import EmailValidator, StringValidator, Validator


class Person(TypedDict):
    name: str = StringValidator(min_length=2)
    email: Annotated[str, EmailValidator()]
    age: int

    @name.process_pre_validate
    def strip_name(self, value: str) -> str:
        return value.strip()


@dataclass
class Signup:
    person: Person = Validator()


def main() -> None:
    row = Signup(person={"name": "  Ada  ", "email": "ada@example.com", "age": 36})
    print(row.person)


if __name__ == "__main__":
    main()
