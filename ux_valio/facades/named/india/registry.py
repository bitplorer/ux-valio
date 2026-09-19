# SPDX-License-Identifier: MIT
"""India registrations (TAN, CIN, Udyam).

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
