# SPDX-License-Identifier: MIT
"""LEI. ISO 17442 20-char identity ∩ mod-97. No GLEIF lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_LEI = re.compile(r"[A-Z0-9]{18}[0-9]{2}")


class LEIValidator(StringValidator):
    """Legal Entity Identifier: 20 chars ∩ ISO 17442 mod-97.

    Usage::

        lei: str = LEIValidator()

    Spaces/hyphens strip; stores uppercase. Format-only is rejected.
    No GLEIF lookup.
    """

    @staticmethod
    def _mod97(text: str) -> bool:
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in text
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_lei(value: Any) -> bool:
        if not isinstance(value, str) or _LEI.fullmatch(value) is None:
            return False
        return LEIValidator._mod97(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_lei(value):
            raise ValueError(f"{self.name} is not a valid LEI")
