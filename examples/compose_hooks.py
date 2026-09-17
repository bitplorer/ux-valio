# SPDX-License-Identifier: MIT
"""Staff profile: ``&`` / ``|`` composition and a before-store strip hook.

Hang ``add_*`` on the descriptor that is the field default: a ``Validator``
facade or the compose **root** after ``&`` / ``AllOf``. Concern leaves do not
carry ``add_*``. ``|`` is OR (``AnyOf``); the root does not AND-run a type
check before alternatives. ``Chain`` is ``AllOf``.
"""

from dataclasses import dataclass

from ux_valio import (
    AllOf,
    AnyOf,
    IntegerValidator,
    LengthValidator,
    RequiredValidator,
    StringValidator,
)

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


def create_profile(
    name: str,
    tag: str,
    note: int | str,
    title: str,
) -> StaffProfile:
    """Create a staff profile. Compose and hook failures raise."""
    return StaffProfile(name=name, tag=tag, note=note, title=title)


def main() -> StaffProfile:
    row = create_profile(name="  Ada  ", tag="ops", note=7, title="Engineer")
    assert row.name == "Ada"
    assert row.note == 7

    other = create_profile(name="Ada", tag="ops", note="n/a", title="Lead")
    assert other.note == "n/a"

    try:
        create_profile(name="Ada", tag="op", note=7, title="Engineer")
    except ValueError:
        pass
    else:
        raise RuntimeError("short tag must raise")

    return row


if __name__ == "__main__":
    created = main()
    print(f"{created.name} tag={created.tag} note={created.note}")
