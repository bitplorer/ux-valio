# SPDX-License-Identifier: MIT
"""IANA timezone key. stdlib ``zoneinfo``. No geo lookup."""

from __future__ import annotations

from typing import Any
from zoneinfo import available_timezones

from ux_valio.facades.typed import StringValidator

_ZONES = available_timezones()


class TimezoneValidator(StringValidator):
    """IANA tz database key (``Asia/Kolkata``, ``UTC``).

    Usage::

        tz: str = TimezoneValidator()

    Stores the key as given (case-sensitive). ``available_timezones()``
    membership — not offsets like ``+05:30``. No geo lookup.
    """

    @staticmethod
    def _is_valid_timezone(value: Any) -> bool:
        return isinstance(value, str) and value in _ZONES

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_timezone(value):
            raise ValueError(f"{self.name} is not a valid IANA timezone")
