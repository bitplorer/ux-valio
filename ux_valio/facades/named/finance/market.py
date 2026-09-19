# SPDX-License-Identifier: MIT
"""Securities / KYB (ISIN, LEI).

Sibling of the other ``finance`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.finance``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_ISIN = re.compile(r"[A-Z]{2}[A-Z0-9]{9}[0-9]")


class ISINValidator(StringValidator):
    """ISIN: ISO 6166, 12 chars ∩ Luhn after A=10…Z=35 expansion.

    Usage::

        isin: str = ISINValidator()

    Print groups strip; stores uppercase compact (``US0378331005``).
    Format-only is rejected. No exchange lookup.
    """

    @staticmethod
    def _luhn_check_digit(body: str) -> str:
        expanded = []
        for char in body:
            if char.isdigit():
                expanded.append(char)
            else:
                expanded.append(str(ord(char) - 55))
        digits = "".join(expanded)
        total = 0
        for index, char in enumerate(reversed(digits)):
            number = int(char)
            if index % 2 == 0:
                number *= 2
                number = number // 10 + number % 10
            total += number
        return str((10 - total % 10) % 10)

    @staticmethod
    def _is_valid_isin(value: Any) -> bool:
        if not isinstance(value, str) or _ISIN.fullmatch(value) is None:
            return False
        return ISINValidator._luhn_check_digit(value[:11]) == value[11]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_isin(value):
            raise ValueError(f"{self.name} is not a valid ISIN")

_LEI = re.compile(r"[A-Z0-9]{18}[0-9]{2}")


class LEIValidator(StringValidator):
    """Legal Entity Identifier: 20 chars ∩ ISO 17442 mod-97.

    Usage::

        lei: str = LEIValidator()

    Spaces/hyphens strip; stores uppercase. Format-only is rejected.
    No GLEIF lookup.
    """

    @staticmethod
    def _mod97(text: str) -> bool:
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in text
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_lei(value: Any) -> bool:
        if not isinstance(value, str) or _LEI.fullmatch(value) is None:
            return False
        return LEIValidator._mod97(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_lei(value):
            raise ValueError(f"{self.name} is not a valid LEI")


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
