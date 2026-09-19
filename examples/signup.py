# SPDX-License-Identifier: MIT
"""Complete registration: signup + login.

One file for the account workflow. Username uniqueness after identity,
password strength via ``AllOf`` (length + digit + letter — Pattern ``&``
concatenates, it is not AND of independent findalls), confirm match on
``post_validate``, hash-on-create on ``post_set``. Login verifies the hash.

Omitted ``collect_all`` / ``debug`` are True. A single failure is that
exception; two or more on one field surface as ``ValidationErrors``.
Per-field, not per-dataclass: the first field that fails still stops later
fields. Team ``seats`` demos multi-concern ``IntegerValidator``.

``PasswordHasher`` is the example port (stdlib ``pbkdf2_hmac``, fixed demo
salt). Production: SQL unique index + bcrypt/argon2id (unique per-row salt).
This file does not ship a DB driver or a crypto library in ``ux_valio``.
"""

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from uuid import UUID, uuid4

from ux_valio import (
    AllOf,
    Digit,
    EmailValidator,
    IntegerValidator,
    Pattern,
    SetOf,
    StringValidator,
    UUIDValidator,
    ValidationErrors,
    Validator,
)


class StoredUser:
    """Row the store keeps. ``password_hash`` is never plaintext."""

    def __init__(self, username: str, email: str, password_hash: str) -> None:
        self.username = username
        self.email = email
        self.password_hash = password_hash


@runtime_checkable
class UserStore(Protocol):
    """Account uniqueness + hashed credential. Production: users table / unique index."""

    def username_taken(self, username: str) -> bool:
        """True when ``username`` is already reserved."""
        ...

    def create(self, username: str, email: str, password_hash: str) -> None:
        """INSERT username, email, hash. Never persist plaintext."""
        ...

    def get(self, username: str) -> StoredUser | None:
        """Return the stored row, or None if missing."""
        ...


@runtime_checkable
class PasswordHasher(Protocol):
    """Password digest. Production: bcrypt / argon2id (unique per-row salt)."""

    def hash(self, plain: str) -> str:
        """Return a digest for ``plain``."""
        ...

    def verify(self, plain: str, hashed: str) -> bool:
        """True when ``plain`` matches ``hashed``."""
        ...


class InMemoryUserStore:
    """Runnable fake. Plug in SQL that satisfies ``UserStore``."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self._users: dict[str, StoredUser] = {}
        for name in taken or ():
            self._users[name.casefold()] = StoredUser(name, "", "")

    def username_taken(self, username: str) -> bool:
        return username.casefold() in self._users

    def create(self, username: str, email: str, password_hash: str) -> None:
        self._users[username.casefold()] = StoredUser(username, email, password_hash)

    def get(self, username: str) -> StoredUser | None:
        return self._users.get(username.casefold())


class Pbkdf2PasswordHasher:
    """Demo hasher (stdlib PBKDF2-HMAC-SHA256, fixed salt).

    Production: replace with bcrypt or argon2id and a unique salt per row.
    The fixed salt is demo-only so the file stays offline and dependency-free.
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


# Pattern ``&`` concatenates. Independent "has a digit" / "has a letter"
# concerns are separate StringValidators under AllOf (findall substring).
password_field = AllOf(
    StringValidator(required=True, min_length=8, max_length=128),
    StringValidator(pattern=Digit(count_min=1)),
    StringValidator(pattern=SetOf(Pattern(r"A-Za-z"), count_min=1)),
)
username_field = StringValidator(required=True, min_length=3, max_length=32)
confirm_field = StringValidator(required=True, min_length=8, max_length=128)
seats_field = IntegerValidator(
    min_value=0,
    max_value=10,
    multiple_of=2,
    required=True,
)
login_username_field = StringValidator(required=True, min_length=1)
login_password_field = StringValidator(required=True, min_length=1)


@dataclass
class SignupForm:
    users: UserStore = field(
        default=Validator[UserStore](required=True),
        repr=False,
        compare=False,
    )
    hasher: PasswordHasher = field(
        default=Validator[PasswordHasher](required=True),
        repr=False,
        compare=False,
    )
    username: str = username_field
    email: str = EmailValidator(required=True)
    password: str = password_field
    password_confirm: str = confirm_field
    display_name: str = StringValidator(max_length=80, default="")
    role: str = Validator(
        in_choice=["member", "moderator", "admin"],
        default="member",
    )
    seats: int = seats_field
    account_id: UUID = UUIDValidator(default_factory=uuid4)

    @username.pre_validate
    def fold_username(self, value: str) -> str:
        return value.strip().casefold()

    @username.post_validate
    def username_available(self, value: str) -> str:
        if self.users.username_taken(value):
            raise ValueError(f"username {value!r} is already registered")
        return value

    @password_confirm.post_validate
    def passwords_match(self, value: str) -> str:
        if value != self.password:
            raise ValueError("password confirmation does not match")
        return value

    @account_id.post_set
    def persist_user(self, value: UUID) -> None:
        self.users.create(
            self.username, self.email, self.hasher.hash(self.password)
        )


@dataclass
class LoginForm:
    users: UserStore = field(
        default=Validator[UserStore](required=True),
        repr=False,
        compare=False,
    )
    hasher: PasswordHasher = field(
        default=Validator[PasswordHasher](required=True),
        repr=False,
        compare=False,
    )
    username: str = login_username_field
    password: str = login_password_field

    @username.pre_validate
    def fold_login_username(self, value: str) -> str:
        return value.strip().casefold()

    @password.post_validate
    def credentials_ok(self, value: str) -> str:
        row = self.users.get(self.username)
        if row is None or not self.hasher.verify(value, row.password_hash):
            raise ValueError("invalid username or password")
        return value


class SignupService:
    """Composition root. Production: ``SignupService(SqlUserStore(dsn), Argon2Hasher())``."""

    def __init__(self, users: UserStore, hasher: PasswordHasher) -> None:
        self.users = users
        self.hasher = hasher

    def register(
        self,
        username: str,
        email: str,
        password: str,
        password_confirm: str,
        seats: int,
        *,
        display_name: str = "",
        role: str = "member",
        account_id: UUID | None = None,
    ) -> SignupForm:
        """Register. Multi-concern failures raise ``ValidationErrors``."""
        kwargs: dict[str, object] = {
            "users": self.users,
            "hasher": self.hasher,
            "username": username,
            "email": email,
            "password": password,
            "password_confirm": password_confirm,
            "display_name": display_name,
            "role": role,
            "seats": seats,
        }
        if account_id is not None:
            kwargs["account_id"] = account_id
        return SignupForm(**kwargs)

    def login(self, username: str, password: str) -> LoginForm:
        """Verify credentials. Unknown user or bad password raise ``ValueError``."""
        return LoginForm(
            users=self.users,
            hasher=self.hasher,
            username=username,
            password=password,
        )


def form_messages(err: Exception) -> list[str]:
    """Map collected failures to caller-facing strings."""
    if isinstance(err, ValidationErrors):
        return [str(item) for item in err.errors]
    return [str(err)]


def _must_raise(fn, *types: type[BaseException]) -> None:
    try:
        fn()
    except types:
        return
    raise AssertionError(f"expected {types}")


def main() -> SignupForm:
    service = SignupService(
        InMemoryUserStore(taken={"taken", "ab"}), Pbkdf2PasswordHasher()
    )
    ok = service.register(
        username="ada",
        email="ada@example.com",
        password="Secret1a",
        password_confirm="Secret1a",
        seats=8,
        display_name="Ada Lovelace",
        role="admin",
    )
    service.login(username="Ada", password="Secret1a")
    _must_raise(
        lambda: service.login(username="ada", password="Wrong1a"), ValueError
    )
    _must_raise(
        lambda: service.register(
            username="taken",
            email="ada@example.com",
            password="Secret1a",
            password_confirm="Secret1a",
            seats=8,
        ),
        ValueError,
        ValidationErrors,
    )
    _must_raise(
        lambda: service.register(
            username="eve",
            email="ada@example.com",
            password="Secret1a",
            password_confirm="Secret1b",
            seats=8,
        ),
        ValueError,
    )
    _must_raise(
        lambda: service.register(
            username="neo",
            email="ada@example.com",
            password="Secret1a",
            password_confirm="Secret1a",
            seats=-3,
        ),
        ValidationErrors,
    )
    return ok


if __name__ == "__main__":
    submitted = main()
    print(f"{submitted.username} seats={submitted.seats}")
