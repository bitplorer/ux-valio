# SPDX-License-Identifier: MIT
"""IBAN Door A facade. ISO 13616 identity ∩ mod-97. No bank lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_IBAN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")


class IBANValidator(StringValidator):
    """Door A string facade: IBAN length 15–34 ∩ rearrange-and-mod-97 == 1."""

    @staticmethod
    def _mod97(text: str) -> bool:
        rearranged = text[4:] + text[:4]
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in rearranged
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_iban(value: Any) -> bool:
        if not isinstance(value, str) or not (15 <= len(value) <= 34):
            return False
        if _IBAN.fullmatch(value) is None:
            return False
        return IBANValidator._mod97(value)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super().pre_validation_processing(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_iban(value):
            raise ValueError(f"{self.name} is not a valid IBAN")
