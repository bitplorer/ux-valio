# SPDX-License-Identifier: MIT
"""VIN. ISO 3779 17-char identity ∩ check digit. No registry lookup."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator

_VIN_MAP = {
    **{str(digit): digit for digit in range(10)},
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)
_FORBIDDEN = set("IOQ")


class VINValidator(StringValidator):
    """Vehicle identification number: ISO 3779, 17 chars ∩ check digit.

    Usage::

        vin: str = VINValidator()

    Spaces/hyphens strip; stores uppercase. ``I`` / ``O`` / ``Q`` forbidden.
    Position 9 is the check (``0–9`` or ``X``). No registry lookup.
    """

    @staticmethod
    def _is_valid_vin(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 17:
            return False
        if any(char in _FORBIDDEN or char not in _VIN_MAP for char in value):
            return False
        total = sum(_VIN_MAP[char] * weight for char, weight in zip(value, _WEIGHTS))
        remainder = total % 11
        check = "X" if remainder == 10 else str(remainder)
        return value[8] == check

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_vin(value):
            raise ValueError(f"{self.name} is not a valid VIN")
