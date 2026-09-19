# SPDX-License-Identifier: MIT
"""Hardware identity (IMEI, MAC). Parallel to catalog.

Does not import sibling named domain modules. Depends on typed
(or the validate door). Public names still re-export from
``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

from typing import Any
from ux_valio.facades.typed import StringValidator
import re

class IMEIValidator(StringValidator):
    """IMEI: 15 digits ∩ Luhn.

    Usage::

        imei: str = IMEIValidator()

    Non-digits strip; stores 15-digit compact. Format-only is rejected.
    No GSMA lookup.
    """

    @staticmethod
    def _luhn_ok(digits: str) -> bool:
        total = 0
        odd = True
        for char in reversed(digits):
            n = int(char)
            if odd := not odd:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def _is_valid_imei(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 15 or not value.isdigit():
            return False
        return IMEIValidator._luhn_ok(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(ch for ch in value if ch.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_imei(value):
            raise ValueError(f"{self.name} is not a valid IMEI")

_MAC = re.compile(r"[0-9A-F]{12}")


class MACAddressValidator(StringValidator):
    """48-bit (6-octet) MAC. Stores 12 uppercase hex digits.

    Usage::

        mac: str = MACAddressValidator()

    Accepts ``aa:bb:cc:dd:ee:ff``, hyphens, Cisco ``aabb.ccdd.eeff``, or
    compact hex. Stores ``AABBCCDDEEFF``. Not EUI-64. No OUI lookup.
    """

    @staticmethod
    def _is_valid_mac(value: Any) -> bool:
        return isinstance(value, str) and _MAC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value.upper() if char in "0123456789ABCDEF")
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_mac(value):
            raise ValueError(f"{self.name} is not a valid MAC address")
