# SPDX-License-Identifier: MIT
"""India person KYC (Aadhaar, PAN, EPIC, passport).

Sibling of the other ``india`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.india``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

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
    """UIDAI Aadhaar: 12 digits ∩ Verhoeff.

    Usage::

        aadhaar: str = AadhaarCardValidator()

    Print form ``2345 6789 0124`` / hyphens strips; stores ``234567890124``.
    First digit is 2–9 (UIDAI; 0 and 1 are reserved). Substring or
    wrong length is rejected. No UIDAI lookup.
    """

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
        if (
            not isinstance(value, str)
            or len(value) != 12
            or not value.isdigit()
            or value[0] in "01"
        ):
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

_PAN = re.compile(r"[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z]")
# Complete A–Z. Do not zip with range(1, 26) — that drops Z.
_A_Z_MAP = {chr(ord("A") + i): i for i in range(26)}
_BASE = 26


class PANCardValidator(StringValidator):
    """Income-tax PAN: 10-char identity ∩ Luhn mod 26.

    Usage::

        pan: str = PANCardValidator()

    Letters case-fold to A–Z; spaces/hyphens strip. Format-only generators
    are rejected. No ITD lookup.
    """

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

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        """ITD letters are case-insensitive. Store the A–Z identity."""
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_pan(instance, value)

    def _validate_pan(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_pan(value):
            raise ValueError(f"{self.name} is not a valid PAN number")

_EPIC = re.compile(r"[A-Z]{3}[0-9]{7}")


class VoterIdValidator(StringValidator):
    """Indian EPIC voter ID: 3 letters + 7 digits.

    Usage::

        epic: str = VoterIdValidator()

    Spaces/hyphens strip; stores uppercase compact (``ABC1234567``).
    No ECI lookup.
    """

    @staticmethod
    def _is_valid_voter_id(value: Any) -> bool:
        return isinstance(value, str) and _EPIC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_voter_id(value):
            raise ValueError(f"{self.name} is not a valid voter ID")


_PASSPORT = re.compile(r"[A-Z][0-9]{7}")


class IndianPassportValidator(StringValidator):
    """Indian passport number: 1 letter + 7 digits.

    Usage::

        passport: str = IndianPassportValidator()

    Spaces/hyphens strip; stores uppercase compact (``A1234567``).
    No MEA lookup.
    """

    @staticmethod
    def _is_valid_passport(value: Any) -> bool:
        return isinstance(value, str) and _PASSPORT.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_passport(value):
            raise ValueError(f"{self.name} is not a valid Indian passport number")
