# SPDX-License-Identifier: MIT
"""Signup form: collect_all plus an injectable uniqueness port.

Default Door A is fail-fast. ``collect_all=True`` with ``debug=True`` surfaces
``ValidationErrors`` for every concern on that descriptor. It is per-field, not
per-dataclass: the first field that fails still stops later fields.

Uniqueness hangs on ``add_validator`` so it joins the collected bag (a short
taken name fails length *and* the store). ``add_post_set`` commits only after
store. Swap ``InMemoryUserStore`` for a SQL unique-index adapter; this file
does not ship a DB driver.
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


USERS: UserStore = InMemoryUserStore()

username_field = StringValidator(
    debug=True,
    required=True,
    min_length=3,
    max_length=32,
    collect_all=True,
)


@dataclass
class SignupForm:
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

    @username_field.add_validator
    def username_available(self, value: str) -> None:
        if USERS.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")

    @username_field.add_post_set
    def commit_username(self, value: str) -> None:
        USERS.commit(value)


def bind_user_store(store: UserStore) -> None:
    """Process composition root. Production: ``bind_user_store(SqlUserStore(dsn))``."""
    global USERS
    USERS = store


def submit_signup(
    username: str,
    email: str,
    seats: int,
    *,
    users: UserStore | None = None,
) -> SignupForm:
    """Submit the form. Multi-concern failures raise ``ValidationErrors``."""
    if users is not None:
        bind_user_store(users)
    return SignupForm(username=username, email=email, seats=seats)


def form_messages(err: ValidationErrors) -> list[str]:
    """Map collected failures to caller-facing strings."""
    return [str(item) for item in err.errors]


def main() -> SignupForm:
    users = InMemoryUserStore(taken={"taken", "ab"})
    ok = submit_signup(username="ada", email="ada@example.com", seats=8, users=users)
    try:
        submit_signup(username="taken", email="ada@example.com", seats=8, users=users)
    except (ValueError, ValidationErrors):
        pass
    try:
        submit_signup(username="ab", email="ada@example.com", seats=8, users=users)
    except ValidationErrors as err:
        form_messages(err)
    try:
        submit_signup(username="eve", email="ada@example.com", seats=7, users=users)
    except ValidationErrors as err:
        form_messages(err)
    try:
        submit_signup(username="neo", email="ada@example.com", seats=-3, users=users)
    except ValidationErrors as err:
        form_messages(err)
    return ok


if __name__ == "__main__":
    submitted = main()
    print(f"{submitted.username} seats={submitted.seats}")
