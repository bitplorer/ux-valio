# SPDX-License-Identifier: MIT
"""IFSC. 11-char RBI identity. No RBI directory lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# Four-letter bank, then 0, then six alphanumeric branch.
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
