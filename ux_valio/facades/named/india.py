# SPDX-License-Identifier: MIT
"""India statutory identity (KYC, tax, bank, GST). Parallel to finance/catalog.

Does not import sibling named domain modules. Depends on typed
(or the validate door). Public names still re-export from
``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

from typing import Any
from ux_valio.facades.typed import StringValidator
import re

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
    Substring or wrong length is rejected. No UIDAI lookup.
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

_GSTIN = re.compile(
    r"(?:0[1-9]|[12][0-9]|3[0-8])[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]"
)
_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class GSTINValidator(StringValidator):
    """GSTIN: 15-char identity ∩ Luhn mod 36.

    Usage::

        gstin: str = GSTINValidator()

    State ``01–38``, then PAN holder, entity, ``Z``, check. Spaces/hyphens
    strip; stores uppercase compact. Format-only is rejected. No GST portal.
    """

    @staticmethod
    def _luhn_mod_36(body: str) -> str:
        factor = 1
        total = 0
        for char in body:
            product = factor * _CHARS.index(char)
            total += product // 36 + product % 36
            factor = 3 - factor
        return _CHARS[(36 - (total % 36)) % 36]

    @staticmethod
    def _is_valid_gstin(value: Any) -> bool:
        if not isinstance(value, str) or _GSTIN.fullmatch(value) is None:
            return False
        return GSTINValidator._luhn_mod_36(value[:14]) == value[14]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_gstin(value):
            raise ValueError(f"{self.name} is not a valid GSTIN")

_TAN = re.compile(r"[A-Z]{3}[ABCFGHLJPT][0-9]{5}[A-Z]")


class TANValidator(StringValidator):
    """Tax Deduction Account Number: 10-char ITD identity.

    Usage::

        tan: str = TANValidator()

    Shape: 3-letter jurisdiction + status (``ABCFGHLJPT``) + 5 digits +
    letter. Spaces/hyphens strip; stores uppercase. No ITD lookup.
    Complements ``PANCardValidator`` / ``GSTINValidator``.
    """

    @staticmethod
    def _is_valid_tan(value: Any) -> bool:
        return isinstance(value, str) and _TAN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_tan(value):
            raise ValueError(f"{self.name} is not a valid TAN")

_CIN = re.compile(r"[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}")


class CINValidator(StringValidator):
    """Corporate Identity Number: 21-char MCA format.

    Usage::

        cin: str = CINValidator()

    ``L``/``U`` + ROC 5 + state 2 + year 4 + class 3 + serial 6.
    Spaces/hyphens strip; stores uppercase. No MCA portal.
    """

    @staticmethod
    def _is_valid_cin(value: Any) -> bool:
        return isinstance(value, str) and _CIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_cin(value):
            raise ValueError(f"{self.name} is not a valid CIN")

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

_IFSC = re.compile(r"[A-Z]{4}0[A-Z0-9]{6}")


class IFSCValidator(StringValidator):
    """Indian Financial System Code: 11-char RBI identity.

    Usage::

        ifsc: str = IFSCValidator()

    Shape ``ABCD0XXXXXX`` (bank 4 + ``0`` + branch 6). Spaces/hyphens
    strip; stores uppercase. No RBI directory lookup.
    """

    @staticmethod
    def _is_valid_ifsc(value: Any) -> bool:
        return isinstance(value, str) and _IFSC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ifsc(value):
            raise ValueError(f"{self.name} is not a valid IFSC")

_PIN = re.compile(r"[1-9][0-9]{5}")


class PinCodeValidator(StringValidator):
    """India Post PIN: 6 digits, first 1–9.

    Usage::

        pin: str = PinCodeValidator()

    Non-digits strip; stores compact ``226001``. No locality lookup.
    """

    @staticmethod
    def _is_valid_pincode(value: Any) -> bool:
        return isinstance(value, str) and _PIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(ch for ch in value if ch.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_pincode(value):
            raise ValueError(f"{self.name} is not a valid Indian PIN code")

_VPA = re.compile(r"[a-z0-9._-]{3,50}@[a-z]{2,20}")


class UPIIdValidator(StringValidator):
    """UPI VPA: ``local@handle`` (NPCI identity).

    Usage::

        vpa: str = UPIIdValidator()

    Spaces strip; stores lowercase (``name@oksbi``). Local 3–50,
    handle 2–20 letters. No PSP lookup.
    """

    @staticmethod
    def _is_valid_upi_id(value: Any) -> bool:
        return isinstance(value, str) and _VPA.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).lower()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_upi_id(value):
            raise ValueError(f"{self.name} is not a valid UPI ID")

_HSN = re.compile(r"(?:\d{4}|\d{6}|\d{8})")


class HSNCodeValidator(StringValidator):
    """India GST HSN/SAC code identity.

    Usage::

        hsn: str = HSNCodeValidator()

    4, 6, or 8 digits (SAC is 6). Non-digits strip; stores compact.
    No GSTN tariff lookup.
    """

    @staticmethod
    def _is_valid_hsn(value: Any) -> bool:
        return isinstance(value, str) and _HSN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_hsn(value):
            raise ValueError(f"{self.name} is not a valid HSN/SAC code")
