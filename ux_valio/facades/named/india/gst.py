# SPDX-License-Identifier: MIT
"""India GST invoice identity (GSTIN, HSN).

Sibling of the other ``india`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.india``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_GSTIN = re.compile(
    r"(?:0[1-9]|[12][0-9]|3[0-8]|97|99)[A-Z]{3}[ABCFGHLJPTK][A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]"
)
_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class GSTINValidator(StringValidator):
    """GSTIN: 15-char identity ∩ Luhn mod 36.

    Usage::

        gstin: str = GSTINValidator()

    State ``01–38`` plus ``97`` (other territory) / ``99`` (centre), then
    PAN holder, entity, ``Z``, check. Spaces/hyphens
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
