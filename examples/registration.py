# SPDX-License-Identifier: MIT
"""Reserve a unique username before store; commit it after store.

Hang uniqueness on ``add_pre_validator`` (return the value). Persist the
reservation on ``add_post_set`` so a failed set does not consume the name.
Do not invent ``add_pre_set``. A uniqueness **task** is the wrong bag.
"""

from dataclasses import dataclass

from ux_valio import StringValidator


class UsernameDirectory:
    """Stand-in for the uniqueness store a registrar would query."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self.taken = set(taken or ())

    def ensure_available(self, username: str) -> str:
        if username in self.taken:
            raise ValueError(f"username {username!r} is already registered")
        return username

    def commit(self, username: str) -> None:
        self.taken.add(username)


directory = UsernameDirectory(taken={"taken"})
username_field = StringValidator(debug=True, required=True, min_length=3)


@dataclass
class Registration:
    username: str = username_field

    @username_field.add_pre_validator
    def username_available(self, value: str) -> str:
        return directory.ensure_available(value)

    @username_field.add_post_set
    def commit_username(self, value: str) -> None:
        directory.commit(value)


def register_username(username: str) -> Registration:
    """Reserve ``username``. Taken or invalid names raise ``ValueError``."""
    return Registration(username=username)


def main() -> Registration:
    directory.taken.clear()
    directory.taken.add("taken")
    row = register_username("fresh")
    assert row.username == "fresh"
    assert "fresh" in directory.taken

    try:
        register_username("taken")
    except ValueError:
        pass
    else:
        raise RuntimeError("taken username must raise")

    try:
        register_username("ab")
    except ValueError:
        pass
    else:
        raise RuntimeError("short username must raise")
    assert "ab" not in directory.taken

    return row


if __name__ == "__main__":
    registered = main()
    print(f"registered {registered.username}")
