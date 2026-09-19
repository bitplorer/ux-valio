# SPDX-License-Identifier: MIT
"""ISIN. ISO 6166 identity ∩ Luhn. No exchange lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_ISIN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")


class ISINValidator(StringValidator):
    """ISIN: ISO 6166, 12 chars ∩ Luhn after A=10…Z=35 expansion.

    Usage::

        isin: str = ISINValidator()

    Print groups strip; stores uppercase compact (``US0378331005``).
    Format-only is rejected. No exchange lookup.
    """

    @staticmethod
    def _luhn_check_digit(body: str) -> str:
        expanded = []
        for char in body:
            if char.isdigit():
                expanded.append(char)
            else:
                expanded.append(str(ord(char) - 55))
        digits = "".join(expanded)
        total = 0
        for index, char in enumerate(reversed(digits)):
            number = int(char)
            if index % 2 == 0:
                number *= 2
                number = number // 10 + number % 10
            total += number
        return str((10 - total % 10) % 10)

    @staticmethod
    def _is_valid_isin(value: Any) -> bool:
        if not isinstance(value, str) or _ISIN.fullmatch(value) is None:
            return False
        return ISINValidator._luhn_check_digit(value[:11]) == value[11]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_isin(value):
            raise ValueError(f"{self.name} is not a valid ISIN")
