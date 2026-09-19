# SPDX-License-Identifier: MIT
"""US securities identity (CUSIP).

Sibling of the other ``us`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.us``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_CUSIP = re.compile(r"[A-Z0-9*@#]{9}")


class CUSIPValidator(StringValidator):
    """CUSIP: 9-char US security id ∩ check digit. Complements ISIN.

    Usage::

        cusip: str = CUSIPValidator()

    Spaces/hyphens strip; stores uppercase. Format-only is rejected.
    No CUSIP bureau lookup.
    """

    @staticmethod
    def _cusip_value(char: str) -> int:
        if char.isdigit():
            return int(char)
        if char.isalpha():
            return ord(char) - 55
        return {"*": 36, "@": 37, "#": 38}[char]

    @staticmethod
    def _is_valid_cusip(value: Any) -> bool:
        if not isinstance(value, str) or _CUSIP.fullmatch(value) is None:
            return False
        total = 0
        for index, char in enumerate(value[:8]):
            number = CUSIPValidator._cusip_value(char)
            if index % 2:
                number *= 2
            total += number // 10 + number % 10
        return str((10 - total % 10) % 10) == value[8]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_cusip(value):
            raise ValueError(f"{self.name} is not a valid CUSIP")

