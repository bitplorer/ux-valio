# SPDX-License-Identifier: MIT
"""Invite a person: TypedDict schema + email uniqueness. No BaseModel.

Hang extras with ``Annotated`` or field-default assignment, then
``@name.pre_validate`` / ``@name.validator`` in the TypedDict body.
``self`` in those hooks is the mapping. Inject ``InviteLog`` on
``InviteService``.
"""

from dataclasses import dataclass
from typing import Annotated, Protocol, TypedDict

from ux_valio import EmailValidator, StringValidator, Validator


class InviteLog(Protocol):
    """Email uniqueness. Production: unique index on invite email."""

    def email_invited(self, email: str) -> bool:
        """True when this email already has an invite."""
        ...

    def commit(self, email: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryInviteLog:
    """Runnable fake. Plug in SQL that satisfies ``InviteLog``."""

    def __init__(self, emails: set[str] | None = None) -> None:
        self._emails = {email.casefold() for email in (emails or set())}

    def email_invited(self, email: str) -> bool:
        return email.casefold() in self._emails

    def commit(self, email: str) -> None:
        self._emails.add(email.casefold())


def _bind(cls, ports, **fields):
    """Wire service ports onto a new instance, then product ``__init__``."""
    inst = object.__new__(cls)
    for name, port in ports.items():
        object.__setattr__(inst, name, port)
    cls.__init__(inst, **fields)
    return inst


class Person(TypedDict):
    name: str = StringValidator(min_length=2, required=True)
    email: Annotated[str, EmailValidator(required=True)]
    age: int

    @name.pre_validate
    def strip_name(self, value: str) -> str:
        return value.strip()

    @name.validator
    def no_digit(self, value: str) -> None:
        if any(char.isdigit() for char in value):
            raise ValueError("name must not contain digits")


@dataclass
class Invite:
    person: Person = Validator()

    @person.post_validate
    def email_free(self, value: Person) -> Person:
        email = value["email"]
        if self.log.email_invited(email):
            raise ValueError(f"email {email!r} already invited")
        return value

    @person.post_set
    def commit_invite(self, value: Person) -> None:
        self.log.commit(value["email"])


class InviteService:
    """Composition root. Production: ``InviteService(SqlInviteLog(pool))``."""

    def __init__(self, log: InviteLog) -> None:
        self.log = log

    def invite(self, name: str, email: str, age: int) -> Invite:
        return _bind(
            Invite,
            {"log": self.log},
            person={"name": name, "email": email, "age": age},
        )


def main() -> Invite:
    taken = InviteService(InMemoryInviteLog(emails={"ada@example.com"}))
    row = InviteService(InMemoryInviteLog()).invite(
        name="  Ada  ", email="ada@example.com", age=36
    )
    try:
        taken.invite(name="Ada", email="ada@example.com", age=36)
    except ValueError:
        pass
    try:
        InviteService(InMemoryInviteLog()).invite(
            name="A1", email="ada@example.com", age=36
        )
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    created = main()
    print(created.person)
