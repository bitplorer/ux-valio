# SPDX-License-Identifier: MIT
"""mypy/pyright: a custom store type needs no AsUser mixin."""

from dataclasses import dataclass

from ux_valio import StringValidator, Validator


class Account:
    def __init__(self, id: str) -> None:
        self.id = id


class AccountValidator(Validator[Account]):
    annotation = Account


@dataclass
class Row:
    name: str = StringValidator(max_length=50)
    owner: Account = AccountValidator()


row = Row(name="ada", owner=Account("a1"))
s: str = row.name
acct: Account = row.owner
