# SPDX-License-Identifier: MIT
"""Open a product user account: identity, role, email, UUID.

Callers copy the dataclass and ``open_account``. Invalid assignment raises
(omitted ``debug`` is True). Assigned ``0`` / ``""`` are kept (not replaced by
``default``). ``default_factory`` builds a per-instance UUID. Username
uniqueness via an injectable ``UserStore`` and hashed passwords via
``PasswordHasher`` live in ``collect_all_form.py`` and ``registration.py``.
"""

from dataclasses import dataclass
from uuid import UUID, uuid4

from ux_valio import (
    EmailValidator,
    IntegerValidator,
    StringValidator,
    UUIDValidator,
    Validator,
)


@dataclass
class UserAccount:
    username: str = StringValidator(
        required=True, min_length=3, max_length=32
    )
    display_name: str = StringValidator(max_length=80, default="")
    role: str = Validator(
        in_choice=["member", "moderator", "admin"],
        default="member",
    )
    reputation: int = IntegerValidator(
        min_value=0, max_value=10_000, default=0
    )
    email: str = EmailValidator(required=True)
    account_id: UUID = UUIDValidator(default_factory=uuid4)


def open_account(
    username: str,
    email: str,
    *,
    display_name: str = "",
    role: str = "member",
    reputation: int = 0,
    account_id: UUID | None = None,
) -> UserAccount:
    """Construct a validated account. ``ValueError`` / ``TypeError`` propagate."""
    kwargs: dict[str, object] = {
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
    account = open_account(
        username="ada",
        email="ada@example.com",
        display_name="Ada Lovelace",
        role="admin",
        reputation=42,
    )
    try:
        open_account(username="ab", email="ada@example.com")
    except ValueError:
        pass
    try:
        open_account(username="ada", email="not-an-email")
    except ValueError:
        pass
    return account


if __name__ == "__main__":
    opened = main()
    print(f"{opened.username} <{opened.email}> role={opened.role}")
