# SPDX-License-Identifier: MIT
"""Goods identity (ISBN/EAN/GTIN/VIN). Parallel to finance/india.

Does not import sibling named domain modules. Depends on typed
(or the validate door). Public names still re-export from
``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

class ISBNValidator(StringValidator):
    """ISBN-10 (mod 11, trailing ``X``) or ISBN-13 (978/979 ∩ EAN check).

    Usage::

        isbn: str = ISBNValidator()

    Hyphens/spaces strip; stores compact (``9780306406157`` / ``0306406152``).
    ISBN-13 without 978/979 is an EAN — use ``EANValidator``. No catalog.
    """

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

class EANValidator(StringValidator):
    """EAN-13: 13 digits ∩ GS1 check.

    Usage::

        ean: str = EANValidator()

    Non-digits strip; stores 13-digit compact. Format-only is rejected.
    978/979 book codes also pass — prefer ``ISBNValidator`` on book fields.
    No GTIN registry.
    """

    @staticmethod
    def _is_valid_ean(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 13 or not value.isdigit():
            return False
        total = sum(
            int(char) * (1 if index % 2 == 0 else 3)
            for index, char in enumerate(value[:12])
        )
        return (10 - total % 10) % 10 == int(value[12])

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ean(value):
            raise ValueError(f"{self.name} is not a valid EAN")

_LEN = frozenset({8, 12, 13, 14})


class GTINValidator(StringValidator):
    """GTIN-8 / UPC-A (12) / EAN-13 / GTIN-14 ∩ GS1 check.

    Usage::

        gtin: str = GTINValidator()

    Non-digits strip; stores compact digits. Format-only is rejected.
    EAN-13 also passes ``EANValidator``; UPC-A does not. No GS1 lookup.
    """

    @staticmethod
    def _is_valid_gtin(value: Any) -> bool:
        if not isinstance(value, str) or len(value) not in _LEN or not value.isdigit():
            return False
        total = 0
        for index, char in enumerate(reversed(value[:-1]), start=1):
            total += int(char) * (3 if index % 2 else 1)
        return str((10 - total % 10) % 10) == value[-1]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_gtin(value):
            raise ValueError(f"{self.name} is not a valid GTIN")

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


_ISSN = re.compile(r"[0-9]{7}[0-9X]")


class ISSNValidator(StringValidator):
    """ISSN: 8 chars ∩ mod-11 (trailing ``X``). Complements ISBN.

    Usage::

        issn: str = ISSNValidator()

    ``0378-5955`` → ``03785955``. Format-only is rejected. No ISSN
    registry lookup.
    """

    @staticmethod
    def _is_valid_issn(value: Any) -> bool:
        if not isinstance(value, str) or _ISSN.fullmatch(value) is None:
            return False
        total = sum(int(value[index]) * (8 - index) for index in range(7))
        check = 11 - (total % 11)
        expect = "0" if check == 11 else ("X" if check == 10 else str(check))
        return value[7] == expect

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_issn(value):
            raise ValueError(f"{self.name} is not a valid ISSN")
