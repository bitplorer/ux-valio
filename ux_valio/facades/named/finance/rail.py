# SPDX-License-Identifier: MIT
"""International bank rails (IBAN, BIC).

Sibling of the other ``finance`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.finance``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# Official ISO 13616 IBAN registry lengths (iban.com/structure, 2026-03-30).
# Unknown country or wrong length is rejected even when mod-97 holds.
_IBAN_LENGTH = {
    "AD": 24, "AE": 23, "AL": 28, "AM": 28, "AT": 20, "AZ": 28, "BA": 20,
    "BE": 16, "BH": 22, "BI": 27, "BG": 22, "BR": 29, "BY": 28, "CH": 21,
    "CR": 22, "CY": 28, "CZ": 24, "DE": 22, "DJ": 27, "DK": 18, "DO": 28,
    "EE": 20, "EG": 29, "ES": 24, "FI": 18, "FK": 18, "FO": 18, "FR": 27,
    "GB": 22, "GE": 22, "GI": 23, "GL": 18, "GR": 27, "GT": 28, "HN": 28,
    "HR": 21, "HU": 28, "IE": 22, "IL": 23, "IQ": 23, "IS": 26, "IT": 27,
    "JO": 30, "KG": 26, "KW": 30, "KZ": 20, "LB": 28, "LC": 32, "LI": 21,
    "LT": 20, "LU": 20, "LV": 21, "LY": 25, "MC": 27, "MD": 24, "ME": 22,
    "MK": 19, "MN": 20, "MR": 27, "MT": 31, "MU": 30, "NI": 28, "NL": 18,
    "NO": 15, "OM": 23, "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29,
    "RO": 24, "RS": 22, "RU": 33, "SA": 24, "SC": 31, "SD": 18, "SE": 24,
    "SI": 19, "SK": 24, "SM": 27, "SO": 23, "ST": 25, "SV": 28, "TJ": 22,
    "TL": 23, "TM": 26, "TN": 24, "TR": 26, "UA": 29, "UZ": 28, "VA": 22,
    "VG": 24, "XK": 20, "YE": 30,
}
_IBAN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")


class IBANValidator(StringValidator):
    """IBAN: ISO 13616 registry length ∩ rearrange-and-mod-97 == 1.

    Usage::

        iban: str = IBANValidator()

    Print groups (``GB82 WEST …``) strip; stores uppercase compact.
    Country length must match the ISO 13616 registry (GB is 22, DE is
    22, NO is 15). Format-only and unknown-country are rejected. No
    bank lookup. Pair with ``BICValidator``.
    """

    @staticmethod
    def _mod97(text: str) -> bool:
        rearranged = text[4:] + text[:4]
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in rearranged
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_iban(value: Any) -> bool:
        if not isinstance(value, str) or _IBAN.fullmatch(value) is None:
            return False
        expected = _IBAN_LENGTH.get(value[:2])
        if expected is None or len(value) != expected:
            return False
        return IBANValidator._mod97(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_iban(value):
            raise ValueError(f"{self.name} is not a valid IBAN")

_BIC = re.compile(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")


class BICValidator(StringValidator):
    """SWIFT/BIC bank identifier (ISO 9362).

    Usage::

        swift: str = BICValidator()

    8 characters (``DEUTDEFF``) or 11 (``DEUTDEFF500``). Spaces/hyphens
    strip; stores uppercase. No SWIFT directory. Pair with ``IBANValidator``.
    """

    @staticmethod
    def _is_valid_bic(value: Any) -> bool:
        return isinstance(value, str) and _BIC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_bic(value):
            raise ValueError(f"{self.name} is not a valid BIC")

