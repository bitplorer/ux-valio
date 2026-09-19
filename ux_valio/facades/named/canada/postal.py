# SPDX-License-Identifier: MIT
"""Canada postal identity.

Sibling of the other ``canada`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.canada``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_CA = re.compile(r"[A-Z]\d[A-Z] \d[A-Z]\d")

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

