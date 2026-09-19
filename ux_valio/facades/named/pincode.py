# SPDX-License-Identifier: MIT
"""India PIN. 6-digit India Post identity. No locality lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# First digit 1–9 (no 0-prefix). Compact 6 digits.
_PIN = re.compile(r"[1-9][0-9]{5}")


class PinCodeValidator(StringValidator):
    """India Post PIN: 6 digits, first 1–9.

    Usage::

        pin: str = PinCodeValidator()

    Non-digits strip; stores compact ``226001``. No locality lookup.
    """

    @staticmethod
    def _is_valid_pincode(value: Any) -> bool:
        return isinstance(value, str) and _PIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(ch for ch in value if ch.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_pincode(value):
            raise ValueError(f"{self.name} is not a valid Indian PIN code")
