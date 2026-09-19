# SPDX-License-Identifier: MIT
"""India payment rails (IFSC, UPI).

Sibling of the other ``india`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.india``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

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
