# SPDX-License-Identifier: MIT
"""Staff profile: ``&`` / ``|`` composition, compose-root hooks, directory port.

Hang ``pre_validate`` / ``task_*`` on the field name (the compose root after ``&`` / ``AllOf``).
``|`` is OR (``AnyOf``); the root does not AND-run a type
check before alternatives. ``Chain`` is ``AllOf``.

Inject ``StaffDirectory`` on ``StaffService``; uniqueness hangs on the
compose-root ``name`` via ``pre_validate``. ``main()`` only runs
the demo. ``InMemoryStaffDirectory`` is the runnable fake; production plugs
HRIS/LDAP. This file does not ship a DB driver.
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


@dataclass
class StaffProfile:
    directory: StaffDirectory
    name: str = StringValidator(max_length=50) & RequiredValidator(
        required=True
    )
    tag: str = LengthValidator(min_length=3) & RequiredValidator(
        required=True
    )
    note: object = AnyOf(
        IntegerValidator(min_value=0),
        StringValidator(min_length=1),
    )
    title: str = AllOf(
        StringValidator(min_length=2, max_length=40),
        RequiredValidator(required=True),
    )

    @name.pre_validate
    def strip_name(self, value: str) -> str:
        return value.strip()

    @name.pre_validate
    def name_available(self, value: str) -> str:
        if self.directory.name_taken(value):
            raise ValueError(f"staff name {value!r} is already in the directory")
        return value

    @name.post_set
    def commit_name(self, value: str) -> None:
        self.directory.commit(value)


class StaffService:
    """Composition root. Production: ``StaffService(LdapDirectory(url))``."""

    def __init__(self, directory: StaffDirectory) -> None:
        self.directory = directory

    def create(
        self, name: str, tag: str, note: int | str, title: str
    ) -> StaffProfile:
        """Create a staff profile. Compose, hook, and directory failures raise."""
        return StaffProfile(
            directory=self.directory, name=name, tag=tag, note=note, title=title
        )


def main() -> StaffProfile:
    service = StaffService(InMemoryStaffDirectory(taken={"Ada"}))
    row = service.create(name="  Grace  ", tag="ops", note=7, title="Engineer")
    StaffService(InMemoryStaffDirectory()).create(
        name="Ada", tag="ops", note="n/a", title="Lead"
    )
    try:
        StaffService(InMemoryStaffDirectory()).create(
            name="Neo", tag="op", note=7, title="Engineer"
        )
    except ValueError:
        pass
    try:
        service.create(name="  Ada  ", tag="ops", note=7, title="Engineer")
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    created = main()
    print(f"{created.name} tag={created.tag} note={created.note}")
