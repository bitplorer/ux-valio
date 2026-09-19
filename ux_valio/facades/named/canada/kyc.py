# SPDX-License-Identifier: MIT
"""Canada person KYC (SIN).

Sibling of the other ``canada`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.canada``.
"""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator


class CanadianSINValidator(StringValidator):
    """Canadian Social Insurance Number: 9 digits ∩ Luhn.

    Usage::

        sin: str = CanadianSINValidator()

    Print groups strip; stores 9 digits. All-zeros placeholder is
    rejected. Starts-with-9 temporary SINs still need Luhn. No
    Service Canada lookup.
    """

    @staticmethod
    def _is_valid_sin(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 9 or not value.isdigit():
            return False
        if value == "000000000":
            return False
        total = 0
        for index, char in enumerate(value):
            number = int(char)
            if index % 2:
                number *= 2
                if number > 9:
                    number -= 9
            total += number
        return total % 10 == 0

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_sin(value):
            raise ValueError(f"{self.name} is not a valid Canadian SIN")
