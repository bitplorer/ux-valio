# SPDX-License-Identifier: MIT
"""EPIC / voter ID. 3 letters + 7 digits. No ECI lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_EPIC = re.compile(r"[A-Z]{3}[0-9]{7}")


class VoterIdValidator(StringValidator):
    """Indian EPIC voter ID: 3 letters + 7 digits.

    Usage::

        epic: str = VoterIdValidator()

    Spaces/hyphens strip; stores uppercase compact (``ABC1234567``).
    No ECI lookup.
    """

    @staticmethod
    def _is_valid_voter_id(value: Any) -> bool:
        return isinstance(value, str) and _EPIC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_voter_id(value):
            raise ValueError(f"{self.name} is not a valid voter ID")
