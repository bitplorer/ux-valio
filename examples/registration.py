# SPDX-License-Identifier: MIT
"""Reserve a unique username before store; commit it after store.

Hang uniqueness on ``add_pre_validator`` (return the value). Persist the
reservation on ``add_post_set`` so a failed set does not consume the name.
Do not invent ``add_pre_set``. A uniqueness **task** is the wrong bag.

``UserStore`` is the injectable port. ``InMemoryUserStore`` is the runnable
fake; production plugs a SQL unique index or Redis SET NX. The full signup
form (collect_all + the same port) is ``collect_all_form.py``.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import StringValidator


class UserStore(Protocol):
    """Username uniqueness. Production: unique index / ``SELECT`` by username."""

    def username_taken(self, username: str) -> bool:
        """True when ``username`` is already reserved."""
        ...

    def commit(self, username: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryUserStore:
    """Runnable fake. Plug in SQL/Redis that satisfies ``UserStore``."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self._taken = {name.casefold(): name for name in (taken or set())}

    def username_taken(self, username: str) -> bool:
        return username.casefold() in self._taken

    def commit(self, username: str) -> None:
        self._taken[username.casefold()] = username


USERS: UserStore = InMemoryUserStore(taken={"taken"})
username_field = StringValidator(debug=True, required=True, min_length=3)


@dataclass
class Registration:
    username: str = username_field

    @username_field.add_pre_validator
    def username_available(self, value: str) -> str:
        if USERS.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")
        return value

    @username_field.add_post_set
    def commit_username(self, value: str) -> None:
        USERS.commit(value)


def bind_user_store(store: UserStore) -> None:
    """Process composition root. Production: ``bind_user_store(SqlUserStore(dsn))``."""
    global USERS
    USERS = store


def register_username(username: str, *, users: UserStore | None = None) -> Registration:
    """Reserve ``username``. Taken or invalid names raise ``ValueError``."""
    if users is not None:
        bind_user_store(users)
    return Registration(username=username)


def main() -> Registration:
    store = InMemoryUserStore(taken={"taken"})
    row = register_username("fresh", users=store)
    try:
        register_username("taken", users=store)
    except ValueError:
        pass
    try:
        register_username("ab", users=store)
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    registered = main()
    print(f"registered {registered.username}")
