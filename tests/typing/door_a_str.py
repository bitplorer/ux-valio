# SPDX-License-Identifier: MIT
"""mypy/pyright Door A: natural ``name: str = StringValidator()``."""

from dataclasses import dataclass

from ux_valio import IntegerValidator, RequiredValidator, StringValidator


@dataclass
class User:
    name: str = StringValidator(debug=True, max_length=50) & RequiredValidator(
        required=True
    )
    age: int = IntegerValidator(debug=True, min_value=0)


u = User(name=" ada ", age=3)
s: str = u.name
n: int = u.age
