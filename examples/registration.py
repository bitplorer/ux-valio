# SPDX-License-Identifier: MIT
"""Register flow: hang uniqueness on add_pre_validator (return the value)."""

from dataclasses import dataclass

from ux_valio import StringValidator

DB = {"taken"}
username_field = StringValidator(debug=True, required=True, min_length=3)


@dataclass
class Register:
    username: str = username_field

    @username_field.add_pre_validator
    def username_not_taken(self, value: str) -> str:
        if value in DB:
            raise ValueError("username already registered")
        return value


def main() -> Register:
    row = Register(username="fresh")
    assert row.username == "fresh"
    return row


if __name__ == "__main__":
    print(main())
