# SPDX-License-Identifier: MIT
"""PAN Door A facade. Identity fullmatch ∩ Luhn mod 26 (complete A–Z map)."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.validators.typed import StringValidator

# Fourth-character holder set includes K (regex, not the docstring list).
_PAN = re.compile(r"[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z]")
# Complete A–Z. Do not zip with range(1, 26) — that drops Z.
_A_Z_MAP = {chr(ord("A") + i): i for i in range(26)}
_BASE = 26


class PANCardValidator(StringValidator):
    """Door A string facade: 10-char PAN identity ∩ Luhn mod 26."""

    @staticmethod
    def _decode_pan_char(char: str) -> int:
        if char.isdigit():
            return int(char)
        return _A_Z_MAP[char]

    @staticmethod
    def _luhn_mod_26(text: str) -> bool:
        digits = [PANCardValidator._decode_pan_char(char) for char in text]
        doubled = (sum(divmod(2 * digit, _BASE)) for digit in digits[-2::-2])
        return (sum(digits[::-2]) + sum(doubled)) % _BASE == 0

    @staticmethod
    def _is_valid_pan(value: Any) -> bool:
        """True only when the whole string matches the PAN shape **and** Luhn mod 26."""
        if not isinstance(value, str):
            return False
        return _PAN.fullmatch(value) is not None and PANCardValidator._luhn_mod_26(value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_pan(instance, value)

    def _validate_pan(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_pan(value):
            raise ValueError(f"{self.name} is not a valid PAN number")
