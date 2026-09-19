# SPDX-License-Identifier: MIT
"""IMEI. 15-digit identity ∩ Luhn. No GSMA lookup."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator


class IMEIValidator(StringValidator):
    """IMEI: 15 digits ∩ Luhn.

    Usage::

        imei: str = IMEIValidator()

    Non-digits strip; stores 15-digit compact. Format-only is rejected.
    No GSMA lookup.
    """

    @staticmethod
    def _luhn_ok(digits: str) -> bool:
        total = 0
        odd = True
        for char in reversed(digits):
            n = int(char)
            if odd := not odd:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def _is_valid_imei(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 15 or not value.isdigit():
            return False
        return IMEIValidator._luhn_ok(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(ch for ch in value if ch.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_imei(value):
            raise ValueError(f"{self.name} is not a valid IMEI")
