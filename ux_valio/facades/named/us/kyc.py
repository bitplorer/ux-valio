# SPDX-License-Identifier: MIT
"""US person / business KYC (SSN, ITIN, EIN).

Sibling of the other ``us`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.us``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_SSN = re.compile(r"(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}")
_ITIN = re.compile(
    r"9\d{2}(?:5[0-9]|6[0-5]|7[0-8]|8[0-8]|9[0-2]|9[4-9])(?!0000)\d{4}"
)
_EIN = re.compile(r"(?!00)\d{9}")


class SSNValidator(StringValidator):
    """US Social Security number: 9 digits, SSA area/group/serial rules.

    Usage::

        ssn: str = SSNValidator()

    ``856-45-6789`` → ``856456789``. Area not ``000`` / ``666`` / ``9xx``;
    group not ``00``; serial not ``0000``. No SSA lookup. ITIN (starts
    ``9``) is ``ITINValidator``.
    """

    @staticmethod
    def _is_valid_ssn(value: Any) -> bool:
        return isinstance(value, str) and _SSN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ssn(value):
            raise ValueError(f"{self.name} is not a valid SSN")


class ITINValidator(StringValidator):
    """US Individual Taxpayer Identification Number: 9 digits.

    Usage::

        itin: str = ITINValidator()

    Starts ``9``; group ``50–65`` / ``70–88`` / ``90–92`` / ``94–99``.
    ``912-70-1234`` → ``912701234``. Complements ``SSNValidator``.
    No IRS lookup.
    """

    @staticmethod
    def _is_valid_itin(value: Any) -> bool:
        return isinstance(value, str) and _ITIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_itin(value):
            raise ValueError(f"{self.name} is not a valid ITIN")


class EINValidator(StringValidator):
    """US Employer Identification Number: 9 digits.

    Usage::

        ein: str = EINValidator()

    ``12-3456789`` → ``123456789``. Prefix ``00`` rejected. No IRS
    prefix-table lookup (the table changes).
    """

    @staticmethod
    def _is_valid_ein(value: Any) -> bool:
        return isinstance(value, str) and _EIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ein(value):
            raise ValueError(f"{self.name} is not a valid EIN")
