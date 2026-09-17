# SPDX-License-Identifier: MIT
"""Staff profile: ``&`` / ``|`` composition, compose-root hooks, directory port.

Hang ``add_*`` on the descriptor that is the field default: a ``Validator``
facade or the compose **root** after ``&`` / ``AllOf``. Concern leaves do not
carry ``add_*``. ``|`` is OR (``AnyOf``); the root does not AND-run a type
check before alternatives. ``Chain`` is ``AllOf``.

``StaffDirectory`` is the injectable uniqueness port hung on the compose-root
``name_field``. ``InMemoryStaffDirectory`` is the runnable fake; production
plugs HRIS/LDAP. This file does not ship a DB driver.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    AllOf,
    AnyOf,
    IntegerValidator,
    LengthValidator,
    RequiredValidator,
    StringValidator,
)


class StaffDirectory(Protocol):
    """Display-name uniqueness. Production: HRIS/LDAP unique CN / email local-part."""

    def name_taken(self, name: str) -> bool:
        """True when ``name`` is already in the directory."""
        ...

    def commit(self, name: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryStaffDirectory:
    """Runnable fake. Plug in HRIS/LDAP that satisfies ``StaffDirectory``."""

    def __init__(self, taken: set[str] | None = None) -> None:
        self._taken = {name.casefold(): name for name in (taken or set())}

    def name_taken(self, name: str) -> bool:
        return name.casefold() in self._taken

    def commit(self, name: str) -> None:
        self._taken[name.casefold()] = name


DIRECTORY: StaffDirectory = InMemoryStaffDirectory()

name_field = StringValidator(debug=True, max_length=50) & RequiredValidator(
    required=True
)
age_or_label = AnyOf(
    IntegerValidator(min_value=0, debug=True),
    StringValidator(min_length=1, debug=True),
)


@dataclass
class StaffProfile:
    name: str = name_field
    tag: str = LengthValidator(min_length=3, debug=True) & RequiredValidator(
        required=True
    )
    note: object = age_or_label
    title: str = AllOf(
        StringValidator(debug=True, min_length=2, max_length=40),
        RequiredValidator(required=True),
    )

    @name_field.add_pre_validator
    def strip_name(self, value: str) -> str:
        return value.strip()

    @name_field.add_validator
    def name_available(self, value: str) -> None:
        if DIRECTORY.name_taken(value):
            raise ValueError(f"staff name {value!r} is already in the directory")

    @name_field.add_post_set
    def commit_name(self, value: str) -> None:
        DIRECTORY.commit(value)


def bind_staff_directory(directory: StaffDirectory) -> None:
    """Process composition root. Production: ``bind_staff_directory(LdapDirectory(url))``."""
    global DIRECTORY
    DIRECTORY = directory


def create_profile(
    name: str,
    tag: str,
    note: int | str,
    title: str,
    *,
    directory: StaffDirectory | None = None,
) -> StaffProfile:
    """Create a staff profile. Compose, hook, and directory failures raise."""
    if directory is not None:
        bind_staff_directory(directory)
    return StaffProfile(name=name, tag=tag, note=note, title=title)


def main() -> StaffProfile:
    directory = InMemoryStaffDirectory(taken={"Ada"})
    row = create_profile(
        name="  Grace  ", tag="ops", note=7, title="Engineer", directory=directory
    )
    create_profile(
        name="Ada", tag="ops", note="n/a", title="Lead", directory=InMemoryStaffDirectory()
    )
    try:
        create_profile(
            name="Neo", tag="op", note=7, title="Engineer", directory=InMemoryStaffDirectory()
        )
    except ValueError:
        pass
    try:
        create_profile(
            name="  Ada  ", tag="ops", note=7, title="Engineer", directory=directory
        )
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    created = main()
    print(f"{created.name} tag={created.tag} note={created.note}")
