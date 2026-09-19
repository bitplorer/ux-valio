# SPDX-License-Identifier: MIT
"""Aadhaar. 12-digit identity ∩ Verhoeff (stdlib tables, no network)."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator

# Verhoeff d / p tables. Identity of the assigned 12-digit string, not findall.
_MULT = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_PERM = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


class AadhaarCardValidator(StringValidator):
    """12 digits ∩ Verhoeff checksum."""

    @staticmethod
    def _verhoeff_ok(digits: str) -> bool:
        try:
            i = len(digits)
            j = 0
            checksum = 0
            while i > 0:
                i -= 1
                checksum = _MULT[checksum][_PERM[j % 8][int(digits[i])]]
                j += 1
            return checksum == 0
        except (ValueError, IndexError):
            return False

    @staticmethod
    def _is_valid_aadhaar(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 12 or not value.isdigit():
            return False
        return AadhaarCardValidator._verhoeff_ok(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        """UIDAI print form is 4-4-4. Store the 12-digit identity."""
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "")
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_aadhaar(instance, value)

    def _validate_aadhaar(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_aadhaar(value):
            raise ValueError(f"{self.name} is not a valid Aadhaar number")
