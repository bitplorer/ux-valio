# SPDX-License-Identifier: MIT
"""MAC address. 48-bit (6-octet) hex identity. No OUI lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

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
