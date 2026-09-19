# SPDX-License-Identifier: MIT
"""Mexico bank rail (CLABE).

Sibling of the other ``mexico`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.mexico``.
"""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator


_CLABE_WEIGHTS = (3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7)


class CLABEValidator(StringValidator):
    """Mexico CLABE: 18 digits ∩ Banxico check. Complements IBAN.

    Usage::

        clabe: str = CLABEValidator()

    Non-digits strip; stores 18 digits. Format-only is rejected. No
    SPEI directory.
    """

    @staticmethod
    def _is_valid_clabe(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 18 or not value.isdigit():
            return False
        total = sum(
            int(char) * weight for char, weight in zip(value[:17], _CLABE_WEIGHTS)
        )
        return str((10 - total % 10) % 10) == value[17]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_clabe(value):
            raise ValueError(f"{self.name} is not a valid CLABE")

