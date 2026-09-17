# SPDX-License-Identifier: MIT
"""Signup form: collect_all plus an injectable uniqueness port.

Default Door A is fail-fast. ``collect_all=True`` with ``debug=True`` surfaces
``ValidationErrors`` for every concern on that descriptor. It is per-field, not
per-dataclass: the first field that fails still stops later fields.

Uniqueness hangs on ``add_pre_validator`` (return the value) so a taken name
is a validation error. ``add_post_set`` commits only after store. Inject
``UserStore`` on ``SignupService``; ``main()`` only runs the demo. Swap
``InMemoryUserStore`` for a SQL unique-index adapter; this file does not ship
a DB driver.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    EmailValidator,
    IntegerValidator,
    StringValidator,
    ValidationErrors,
)


class UserStore(Protocol):
    """Username uniqueness. Production: ``SELECT 1 FROM users WHERE username=$1``."""

    def username_taken(self, username: str) -> bool:
        """True when ``username`` is already reserved."""
        ...

    def commit(self, username: str) -> None:
        """Persist after a successful set. Production: INSERT / Redis SET NX."""
        ...


class InMemoryUserStore:
    """Runnable fake. Plug in SQL/Redis that satisfies ``UserStore``."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self._taken = {name.casefold(): name for name in (taken or set())}

    def username_taken(self, username: str) -> bool:
        return username.casefold() in self._taken

    def commit(self, username: str) -> None:
        self._taken[username.casefold()] = username


username_field = StringValidator(
    debug=True,
    required=True,
    min_length=3,
    max_length=32,
    collect_all=True,
)


@dataclass
class SignupForm:
    users: UserStore
    username: str = username_field
    email: str = EmailValidator(debug=True, required=True, collect_all=True)
    seats: int = IntegerValidator(
        min_value=0,
        max_value=10,
        multiple_of=2,
        collect_all=True,
        debug=True,
        required=True,
    )

    @username_field.add_pre_validator
    def username_available(self, value: str) -> str:
        if self.users.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")
        return value

    @username_field.add_post_set
    def commit_username(self, value: str) -> None:
        self.users.commit(value)


class SignupService:
    """Composition root. Production: ``SignupService(SqlUserStore(dsn))``."""

    def __init__(self, users: UserStore) -> None:
        self.users = users

    def submit(self, username: str, email: str, seats: int) -> SignupForm:
        """Submit the form. Multi-concern failures raise ``ValidationErrors``."""
        return SignupForm(
            users=self.users, username=username, email=email, seats=seats
        )


def form_messages(err: ValidationErrors) -> list[str]:
    """Map collected failures to caller-facing strings."""
    return [str(item) for item in err.errors]


def main() -> SignupForm:
    service = SignupService(InMemoryUserStore(taken={"taken", "ab"}))
    ok = service.submit(username="ada", email="ada@example.com", seats=8)
    try:
        service.submit(username="taken", email="ada@example.com", seats=8)
    except (ValueError, ValidationErrors):
        pass
    try:
        service.submit(username="ab", email="ada@example.com", seats=8)
    except (ValueError, ValidationErrors) as err:
        if isinstance(err, ValidationErrors):
            form_messages(err)
    try:
        service.submit(username="eve", email="ada@example.com", seats=7)
    except ValidationErrors as err:
        form_messages(err)
    try:
        service.submit(username="neo", email="ada@example.com", seats=-3)
    except ValidationErrors as err:
        form_messages(err)
    return ok


if __name__ == "__main__":
    submitted = main()
    print(f"{submitted.username} seats={submitted.seats}")
