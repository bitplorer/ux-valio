# SPDX-License-Identifier: MIT
"""ULID. 26-char Crockford base32. No monotonic / clock check."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

# Crockford: no I, L, O, U. First char 0–7 (48-bit timestamp).
_ULID = re.compile(r"[0-7][0-9A-HJKMNP-TV-Z]{25}")


class ULIDValidator(StringValidator):
    """ULID public id (26 chars). Complements ``UUIDValidator``.

    Usage::

        public_id: str = ULIDValidator()

    Stores uppercase. ``I`` / ``L`` / ``O`` / ``U`` rejected. No
    timestamp-range check beyond the first-char 0–7 rule.
    """

    @staticmethod
    def _is_valid_ulid(value: Any) -> bool:
        return isinstance(value, str) and _ULID.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_ulid(value):
            raise ValueError(f"{self.name} is not a valid ULID")
