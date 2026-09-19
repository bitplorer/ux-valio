# SPDX-License-Identifier: MIT
"""HSN / SAC. GST tariff 4, 6, or 8 digits. No GSTN lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_HSN = re.compile(r"(?:\d{4}|\d{6}|\d{8})")


class HSNCodeValidator(StringValidator):
    """India GST HSN/SAC code identity.

    Usage::

        hsn: str = HSNCodeValidator()

    4, 6, or 8 digits (SAC is 6). Non-digits strip; stores compact.
    No GSTN tariff lookup.
    """

    @staticmethod
    def _is_valid_hsn(value: Any) -> bool:
        return isinstance(value, str) and _HSN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_hsn(value):
            raise ValueError(f"{self.name} is not a valid HSN/SAC code")
