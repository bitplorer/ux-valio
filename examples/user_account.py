# SPDX-License-Identifier: MIT
"""User profile: string / integer / email / UUID / choice on Door A."""

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
    username: str = StringValidator(debug=True, required=True, min_length=3, max_length=32)
    display: str = StringValidator(debug=True, max_length=80, default="")
    rank: str = Validator(
        in_choice=["Member", "Moderator", "Admin"], default="Member", debug=True
    )
    karma: int = IntegerValidator(min_value=0, max_value=10_000, default=0, debug=True)
    email: str = EmailValidator(debug=True, required=True)
    account_id: UUID = UUIDValidator(debug=True, required=True)


def main() -> UserAccount:
    user = UserAccount(
        username="ada",
        display="Ada Lovelace",
        rank="Admin",
        karma=42,
        email="ada@example.com",
        account_id=uuid4(),
    )
    assert user.username == "ada"
    assert user.rank == "Admin"
    return user


if __name__ == "__main__":
    print(main())
