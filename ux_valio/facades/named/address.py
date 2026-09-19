# SPDX-License-Identifier: MIT
"""Postal identity (US ZIP, CA, UK). Complements India ``PinCodeValidator``.

Does not import sibling named domain modules. Depends on typed.
Public names re-export from ``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_US_ZIP = re.compile(r"[0-9]{5}(?:[0-9]{4})?")
_CA = re.compile(r"[A-Z]\d[A-Z] \d[A-Z]\d")
_UK = re.compile(
    r"(?:GIR 0AA|[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2})"
)


class USZipCodeValidator(StringValidator):
    """US ZIP: 5 digits or ZIP+4.

    Usage::

        zip: str = USZipCodeValidator()

    ``90210-1234`` → ``902101234``. No USPS lookup.
    """

    @staticmethod
    def _is_valid_zip(value: Any) -> bool:
        return isinstance(value, str) and _US_ZIP.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_zip(value):
            raise ValueError(f"{self.name} is not a valid US ZIP code")


class CAPostalCodeValidator(StringValidator):
    """Canadian postal code: ``A1A 1A1``.

    Usage::

        postal: str = CAPostalCodeValidator()

    Stores uppercase with the official space. No Canada Post lookup.
    """

    @staticmethod
    def _is_valid_ca_postal(value: Any) -> bool:
        return isinstance(value, str) and _CA.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            compact = "".join(value.split()).upper()
            if len(compact) == 6:
                value = f"{compact[:3]} {compact[3:]}"
            else:
                value = compact
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ca_postal(value):
            raise ValueError(f"{self.name} is not a valid Canadian postal code")


class UKPostcodeValidator(StringValidator):
    """UK postcode (Royal Mail outward + inward).

    Usage::

        postcode: str = UKPostcodeValidator()

    Stores uppercase with one space (``SW1A 1AA``). No Royal Mail lookup.
    """

    @staticmethod
    def _is_valid_uk_postcode(value: Any) -> bool:
        return isinstance(value, str) and _UK.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            compact = "".join(value.split()).upper()
            if len(compact) >= 5:
                value = f"{compact[:-3]} {compact[-3:]}"
            else:
                value = compact
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_uk_postcode(value):
            raise ValueError(f"{self.name} is not a valid UK postcode")
