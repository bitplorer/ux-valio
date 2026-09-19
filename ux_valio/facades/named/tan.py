# SPDX-License-Identifier: MIT
"""TAN. Income-tax deduction identity. No ITD lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# Jurisdiction 3 + status (company/person/…) + 5 digits + letter.
_TAN = re.compile(r"[A-Z]{3}[ABCFGHLJPT][0-9]{5}[A-Z]")


class TANValidator(StringValidator):
    """10-char TAN identity. Complements ``PANCardValidator`` / ``GSTINValidator``."""

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
