# SPDX-License-Identifier: MIT
"""Open a product user account: identity, role, email, UUID.

Callers copy the dataclass and ``open_account``. ``debug=True`` is fail-closed:
invalid assignment raises. Assigned ``0`` / ``""`` are kept (not replaced by
``default``). ``default_factory`` builds a per-instance UUID.
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
        debug=True, required=True, min_length=3, max_length=32
    )
    display_name: str = StringValidator(debug=True, max_length=80, default="")
    role: str = Validator(
        in_choice=["member", "moderator", "admin"],
        default="member",
        debug=True,
    )
    reputation: int = IntegerValidator(
        min_value=0, max_value=10_000, default=0, debug=True
    )
    email: str = EmailValidator(debug=True, required=True)
    account_id: UUID = UUIDValidator(debug=True, default_factory=uuid4)


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
    assert account.username == "ada"
    assert account.role == "admin"
    assert isinstance(account.account_id, UUID)

    try:
        open_account(username="ab", email="ada@example.com")
    except ValueError:
        pass
    else:
        raise RuntimeError("short username must raise")

    try:
        open_account(username="ada", email="not-an-email")
    except ValueError:
        pass
    else:
        raise RuntimeError("invalid email must raise")

    return account


if __name__ == "__main__":
    opened = main()
    print(f"{opened.username} <{opened.email}> role={opened.role}")
