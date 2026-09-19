# SPDX-License-Identifier: MIT
"""EAN-13. GS1 check digit. No GTIN registry lookup."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator


class EANValidator(StringValidator):
    """EAN-13: 13 digits ∩ GS1 check.

    Usage::

        ean: str = EANValidator()

    Non-digits strip; stores 13-digit compact. Format-only is rejected.
    978/979 book codes also pass — prefer ``ISBNValidator`` on book fields.
    No GTIN registry.
    """

    @staticmethod
    def _is_valid_ean(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 13 or not value.isdigit():
            return False
        total = sum(
            int(char) * (1 if index % 2 == 0 else 3)
            for index, char in enumerate(value[:12])
        )
        return (10 - total % 10) % 10 == int(value[12])

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ean(value):
            raise ValueError(f"{self.name} is not a valid EAN")
