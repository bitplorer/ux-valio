# SPDX-License-Identifier: MIT
"""Compose roots and hooks: hang add_* on the descriptor that is the default."""

from dataclasses import dataclass

from ux_valio import (
    IntegerValidator,
    LengthValidator,
    RequiredValidator,
    StringValidator,
)

name_field = StringValidator(debug=True, max_length=50) & RequiredValidator(required=True)
age_or_label = IntegerValidator(min_value=0, debug=True) | StringValidator(
    min_length=1, debug=True
)


@dataclass
class Profile:
    name: str = name_field
    tag: str = LengthValidator(min_length=3, debug=True) & RequiredValidator(required=True)
    note: object = age_or_label

    @name_field.add_pre_validator
    def strip_name(self, value: str) -> str:
        return value.strip()


def main() -> Profile:
    row = Profile(name="  Ada  ", tag="ops", note=7)
    assert row.name == "Ada"
    other = Profile(name="Ada", tag="ops", note="n/a")
    assert other.note == "n/a"
    return row


if __name__ == "__main__":
    print(main())
