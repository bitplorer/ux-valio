# SPDX-License-Identifier: MIT
"""GTIN. GS1 8/12/13/14 ∩ check digit. No GTIN registry."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator

_LEN = frozenset({8, 12, 13, 14})


class GTINValidator(StringValidator):
    """GTIN-8 / UPC-A (12) / EAN-13 / GTIN-14 ∩ GS1 check.

    Usage::

        gtin: str = GTINValidator()

    Non-digits strip; stores compact digits. Format-only is rejected.
    EAN-13 also passes ``EANValidator``; UPC-A does not. No GS1 lookup.
    """

    @staticmethod
    def _is_valid_gtin(value: Any) -> bool:
        if not isinstance(value, str) or len(value) not in _LEN or not value.isdigit():
            return False
        total = 0
        for index, char in enumerate(reversed(value[:-1]), start=1):
            total += int(char) * (3 if index % 2 else 1)
        return str((10 - total % 10) % 10) == value[-1]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_gtin(value):
            raise ValueError(f"{self.name} is not a valid GTIN")
