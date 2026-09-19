# SPDX-License-Identifier: MIT
"""BIC (ISO 9362 / SWIFT). 8- or 11-char bank identity. No directory lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# Bank 4 + country 2 + location 2 + optional branch 3.
_BIC = re.compile(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")


class BICValidator(StringValidator):
    """SWIFT/BIC identity. Complements ``IBANValidator``."""

    @staticmethod
    def _is_valid_bic(value: Any) -> bool:
        return isinstance(value, str) and _BIC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_bic(value):
            raise ValueError(f"{self.name} is not a valid BIC")
