# SPDX-License-Identifier: MIT
"""Open a product user account: identity, role, email, UUID.

Username uniqueness hangs on ``pre_validate`` (not a second “blank”
check — ``required`` / ``min_length`` already own None and short
strings). Inject ``AccountDirectory`` on ``AccountService``. Hashed
passwords live in ``collect_all_form.py`` / ``registration.py``.
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


@dataclass
class UserAccount:
    directory: AccountDirectory
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

    @username.pre_validate
    def username_available(self, value: str) -> str:
        if self.directory.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")
        return value

    @username.post_set
    def commit_username(self, value: str) -> None:
        self.directory.commit(value)


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
            "directory": self.directory,
            "username": username,
            "display_name": display_name,
            "role": role,
            "reputation": reputation,
            "email": email,
        }
        if account_id is not None:
            kwargs["account_id"] = account_id
        return UserAccount(**kwargs)


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
