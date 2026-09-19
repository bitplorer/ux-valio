# SPDX-License-Identifier: MIT
"""Open a product user account: identity, role, email, UUID.

Username uniqueness hangs on ``post_validate`` (after ``required`` /
``min_length``). Persist on ``post_set``. ``directory`` is the injected
store — one shared instance from ``AccountService``, not an ``__init__``
field.
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from ux_valio import (
    EmailValidator,
    IntegerValidator,
    StringValidator,
    UUIDValidator,
    Validator,
)


class AccountDirectory(Protocol):
    """Username uniqueness. Production: unique index on ``username``."""

    def username_taken(self, username: str) -> bool:
        """True when this username is already on file."""
        ...

    def commit(self, username: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryAccountDirectory:
    """Runnable fake. Plug in SQL that satisfies ``AccountDirectory``."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self._taken = {name.casefold() for name in (taken or set())}

    def username_taken(self, username: str) -> bool:
        return username.casefold() in self._taken

    def commit(self, username: str) -> None:
        self._taken.add(username.casefold())


def _bind(cls, ports, **fields):
    """Wire service ports onto a new instance, then product ``__init__``."""
    inst = object.__new__(cls)
    for name, port in ports.items():
        object.__setattr__(inst, name, port)
    cls.__init__(inst, **fields)
    return inst


@dataclass
class UserAccount:
    username: str = StringValidator(required=True, min_length=3, max_length=32)
    display_name: str = StringValidator(max_length=80, default="")
    role: str = Validator(
        in_choice=["member", "moderator", "admin"],
        default="member",
    )
    reputation: int = IntegerValidator(min_value=0, max_value=10_000, default=0)
    email: str = EmailValidator(required=True)
    account_id: UUID = UUIDValidator(default_factory=uuid4)

    @username.pre_validate
    def fold_username(self, value: str) -> str:
        return value.strip().casefold()

    @username.post_validate
    def username_available(self, value: str) -> str:
        if self.directory.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")
        return value

    @email.post_set
    def commit_username(self, value: str) -> None:
        self.directory.commit(self.username)


class AccountService:
    """Composition root. Production: ``AccountService(SqlAccountDirectory(pool))``."""

    def __init__(self, directory: AccountDirectory) -> None:
        self.directory = directory

    def open(
        self,
        username: str,
        email: str,
        *,
        display_name: str = "",
        role: str = "member",
        reputation: int = 0,
        account_id: UUID | None = None,
    ) -> UserAccount:
        kwargs: dict[str, object] = {
            "username": username,
            "display_name": display_name,
            "role": role,
            "reputation": reputation,
            "email": email,
        }
        if account_id is not None:
            kwargs["account_id"] = account_id
        return _bind(UserAccount, {"directory": self.directory}, **kwargs)


def main() -> UserAccount:
    service = AccountService(InMemoryAccountDirectory(taken={"ada"}))
    account = AccountService(InMemoryAccountDirectory()).open(
        username="  Grace  ",
        email="grace@example.com",
        display_name="Grace Hopper",
        role="admin",
        reputation=42,
    )
    try:
        service.open(username="Ada", email="ada@example.com")
    except ValueError:
        pass
    try:
        AccountService(InMemoryAccountDirectory()).open(
            username="ab", email="ada@example.com"
        )
    except ValueError:
        pass
    try:
        AccountService(InMemoryAccountDirectory()).open(
            username="neo", email="not-an-email"
        )
    except ValueError:
        pass
    return account


if __name__ == "__main__":
    opened = main()
    print(f"{opened.username} <{opened.email}> role={opened.role}")
