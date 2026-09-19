# SPDX-License-Identifier: MIT
"""ISBN-10 / ISBN-13. Checksum identity. No catalog lookup."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator


class ISBNValidator(StringValidator):
    """ISBN-10 (mod 11, ``X``) or ISBN-13 (978/979 ∩ EAN check). Compact store."""

    @staticmethod
    def _isbn10_ok(digits: str) -> bool:
        if len(digits) != 10:
            return False
        total = 0
        for index, char in enumerate(digits[:9]):
            if not char.isdigit():
                return False
            total += int(char) * (10 - index)
        check = digits[9]
        check_value = 10 if check == "X" else (int(check) if check.isdigit() else -1)
        if check_value < 0:
            return False
        return (total + check_value) % 11 == 0

    @staticmethod
    def _isbn13_ok(digits: str) -> bool:
        if len(digits) != 13 or not digits.isdigit():
            return False
        if digits[:3] not in {"978", "979"}:
            return False
        total = sum(int(char) * (1 if index % 2 == 0 else 3) for index, char in enumerate(digits[:12]))
        return (10 - total % 10) % 10 == int(digits[12])

    @staticmethod
    def _is_valid_isbn(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return ISBNValidator._isbn10_ok(value) or ISBNValidator._isbn13_ok(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value.upper() if char.isalnum())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_isbn(value):
            raise ValueError(f"{self.name} is not a valid ISBN")
