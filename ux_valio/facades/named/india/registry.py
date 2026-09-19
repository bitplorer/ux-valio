# SPDX-License-Identifier: MIT
"""India registrations (TAN, CIN, Udyam, DIN, LLPIN, FSSAI).

Sibling of the other ``india`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.india``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

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

_UDYAM = re.compile(r"UDYAM-[A-Z]{2}-\d{2}-\d{7}")


class UdyamValidator(StringValidator):
    """Udyam MSME registration identity.

    Usage::

        udyam: str = UdyamValidator()

    ``UDYAM-MH-00-0000001`` — state 2, district 2, serial 7. Spaces
    strip; stores uppercase. No MSME portal lookup.
    """

    @staticmethod
    def _is_valid_udyam(value: Any) -> bool:
        return isinstance(value, str) and _UDYAM.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_udyam(value):
            raise ValueError(f"{self.name} is not a valid Udyam registration")


_DIN = re.compile(r"[0-9]{8}")


class DINValidator(StringValidator):
    """MCA Director Identification Number: 8 digits.

    Usage::

        din: str = DINValidator()

    Leading zeros stay (early DINs). No check digit; no MCA lookup.
    """

    @staticmethod
    def _is_valid_din(value: Any) -> bool:
        return isinstance(value, str) and _DIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_din(value):
            raise ValueError(f"{self.name} is not a valid DIN")


_LLPIN = re.compile(r"[A-Z]{3}[0-9]{4}")


class LLPINValidator(StringValidator):
    """MCA LLP Identification Number: ``AAA-1234``.

    Usage::

        llpin: str = LLPINValidator()

    Hyphen optional; stores compact ``AAA1234``. No MCA lookup.
    """

    @staticmethod
    def _is_valid_llpin(value: Any) -> bool:
        return isinstance(value, str) and _LLPIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_llpin(value):
            raise ValueError(f"{self.name} is not a valid LLPIN")


_FSSAI = re.compile(r"[12](?:00|0[1-9]|[12][0-9]|3[0-8])[0-9]{11}")


class FSSAIValidator(StringValidator):
    """FSSAI licence / registration: 14 digits.

    Usage::

        fssai: str = FSSAIValidator()

    First digit ``1`` licence / ``2`` registration; next two state
    (``00`` central, else ``01–38``). Stores compact digits. No FoSCoS
    lookup. FSSAI publishes no check digit.
    """

    @staticmethod
    def _is_valid_fssai(value: Any) -> bool:
        return isinstance(value, str) and _FSSAI.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_fssai(value):
            raise ValueError(f"{self.name} is not a valid FSSAI number")
