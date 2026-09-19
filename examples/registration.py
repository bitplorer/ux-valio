# SPDX-License-Identifier: MIT
"""Reserve a unique username with password hash before store.

Hang uniqueness on ``process_pre_validate`` (return the value). Confirm match
on the same hook. Persist the hashed password on ``process_post_set`` of the
last field so a failed set does not consume the name and persist fail-closed.
``task_post_set`` is background (welcome email), not persist. Do not invent
``add_pre_set``.

Inject ``UserStore`` and ``PasswordHasher`` on ``RegistrationService``;
``main()`` only runs the demo. Full collect_all signup + login lives in
``collect_all_form.py``. Production: unique index + bcrypt/argon2.
"""

import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional, Protocol

from ux_valio import (
    AllOf,
    Digit,
    Pattern,
    SetOf,
    StringValidator,
)


class StoredUser:
    """Row the store keeps. ``password_hash`` is never plaintext."""

    def __init__(self, username: str, email: str, password_hash: str) -> None:
        self.username = username
        self.email = email
        self.password_hash = password_hash


class UserStore(Protocol):
    """Username uniqueness + hashed credential. Production: unique index."""

    def username_taken(self, username: str) -> bool:
        """True when ``username`` is already reserved."""
        ...

    def create(self, username: str, email: str, password_hash: str) -> None:
        """INSERT username and hash. Never persist plaintext."""
        ...

    def get(self, username: str) -> Optional[StoredUser]:
        """Return the stored row, or None if missing."""
        ...


class PasswordHasher(Protocol):
    """Password digest. Production: bcrypt / argon2id (unique per-row salt)."""

    def hash(self, plain: str) -> str:
        """Return a digest for ``plain``."""
        ...

    def verify(self, plain: str, hashed: str) -> bool:
        """True when ``plain`` matches ``hashed``."""
        ...


class InMemoryUserStore:
    """Runnable fake. Plug in SQL/Redis that satisfies ``UserStore``."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self._users: dict[str, StoredUser] = {}
        for name in taken or ():
            self._users[name.casefold()] = StoredUser(name, "", "")

    def username_taken(self, username: str) -> bool:
        return username.casefold() in self._users

    def create(self, username: str, email: str, password_hash: str) -> None:
        self._users[username.casefold()] = StoredUser(username, email, password_hash)

    def get(self, username: str) -> Optional[StoredUser]:
        return self._users.get(username.casefold())


class Pbkdf2PasswordHasher:
    """Demo hasher (stdlib PBKDF2-HMAC-SHA256, fixed salt).

    Production: replace with bcrypt or argon2id and a unique salt per row.
    """

    def __init__(
        self, salt: bytes = b"ux-valio-demo-salt", rounds: int = 100_000
    ) -> None:
        self.salt = salt
        self.rounds = rounds

    def hash(self, plain: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", plain.encode("utf-8"), self.salt, self.rounds
        ).hex()

    def verify(self, plain: str, hashed: str) -> bool:
        if not hashed:
            return False
        return hmac.compare_digest(self.hash(plain), hashed)


@dataclass
class Registration:
    users: UserStore
    hasher: PasswordHasher
    username: str = StringValidator(required=True, min_length=3)
    password: str = AllOf(
        StringValidator(required=True, min_length=8, max_length=128),
        StringValidator(pattern=Digit(count_min=1)),
        StringValidator(pattern=SetOf(Pattern(r"A-Za-z"), count_min=1)),
    )
    password_confirm: str = StringValidator(
        required=True, min_length=8, max_length=128
    )

    @username.process_pre_validate
    def username_available(self, value: str) -> str:
        if self.users.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")
        return value

    @password_confirm.process_pre_validate
    def passwords_match(self, value: str) -> str:
        if value != self.password:
            raise ValueError("password confirmation does not match")
        return value

    @password_confirm.process_post_set
    def persist_user(self, value: str) -> None:
        self.users.create(self.username, "", self.hasher.hash(self.password))


class RegistrationService:
    """Composition root. Production: ``RegistrationService(SqlUserStore(dsn), Argon2Hasher())``."""

    def __init__(self, users: UserStore, hasher: PasswordHasher) -> None:
        self.users = users
        self.hasher = hasher

    def register(
        self, username: str, password: str, password_confirm: str
    ) -> Registration:
        """Reserve ``username`` with a hashed password. Failures raise ``ValueError``."""
        return Registration(
            users=self.users,
            hasher=self.hasher,
            username=username,
            password=password,
            password_confirm=password_confirm,
        )


def main() -> Registration:
    service = RegistrationService(
        InMemoryUserStore(taken={"taken"}), Pbkdf2PasswordHasher()
    )
    row = service.register("fresh", "Secret1a", "Secret1a")
    try:
        service.register("taken", "Secret1a", "Secret1a")
    except ValueError:
        pass
    try:
        service.register("ab", "Secret1a", "Secret1a")
    except ValueError:
        pass
    try:
        service.register("other", "Secret1a", "Secret1b")
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    registered = main()
    print(f"registered {registered.username}")
