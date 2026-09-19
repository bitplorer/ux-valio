# SPDX-License-Identifier: MIT
"""mypy/pyright: annotate the descriptor; instance is str."""

from dataclasses import dataclass

from ux_valio import IntegerValidator, StringValidator, Validator


@dataclass
class User:
    name: StringValidator = StringValidator(debug=True, max_length=50)
    age: Validator[int] = IntegerValidator(debug=True, min_value=0)

    @name.process_pre_validate
    def strip(self, value: str) -> str:
        return value.strip()


u = User(name=" ada ", age=3)
s: str = u.name
n: int = u.age
User.name.process_pre_validate(lambda inst, val: val)
