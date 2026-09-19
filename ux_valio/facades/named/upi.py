# SPDX-License-Identifier: MIT
"""UPI VPA Door A facade. NPCI handle identity. No PSP lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# Local 3–50, handle 2–20 letters (oksbi, ybl, paytm, apl).
_VPA = re.compile(r"[a-z0-9._-]{3,50}@[a-z]{2,20}")


class UPIIdValidator(StringValidator):
    """Door A string facade: UPI virtual payment address identity."""

    @staticmethod
    def _is_valid_upi_id(value: Any) -> bool:
        return isinstance(value, str) and _VPA.fullmatch(value) is not None

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).lower()
        return super().pre_validation_processing(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_upi_id(value):
            raise ValueError(f"{self.name} is not a valid UPI ID")
