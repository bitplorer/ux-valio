# SPDX-License-Identifier: MIT
"""GSTIN Door A facade. 15-char identity ∩ Luhn mod 36. No GST portal."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# SS + PAN holder set + entity + Z + check. State 01–38. No network.
_GSTIN = re.compile(
    r"(?:0[1-9]|[12][0-9]|3[0-8])[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]"
)
_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class GSTINValidator(StringValidator):
    """Door A string facade: GSTIN format ∩ Luhn mod 36 checksum."""

    @staticmethod
    def _luhn_mod_36(body: str) -> str:
        factor = 1
        total = 0
        for char in body:
            product = factor * _CHARS.index(char)
            total += product // 36 + product % 36
            factor = 3 - factor
        return _CHARS[(36 - (total % 36)) % 36]

    @staticmethod
    def _is_valid_gstin(value: Any) -> bool:
        if not isinstance(value, str) or _GSTIN.fullmatch(value) is None:
            return False
        return GSTINValidator._luhn_mod_36(value[:14]) == value[14]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_gstin(value):
            raise ValueError(f"{self.name} is not a valid GSTIN")
