# SPDX-License-Identifier: MIT
"""CIN. 21-char MCA company identity. No MCA portal lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# L/U listed, 5-digit ROC, state, year, class (PLC/PTC/…), serial.
_CIN = re.compile(r"[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}")


class CINValidator(StringValidator):
    """Corporate Identity Number format identity."""

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
