# SPDX-License-Identifier: MIT
"""Card MM/YY print form. Not ``ExpiryValidator`` (that is wall-clock)."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_MMYY = re.compile(r"(0[1-9]|1[0-2])[0-9]{2}")


class CardExpiryValidator(StringValidator):
    """Payment-card month/year as printed. Stores ``MMYY``.

    Usage::

        exp: str = CardExpiryValidator()

    Accepts ``12/25``, ``12-25``, ``1225``. Does **not** reject a past
    month — hang ``ExpiryValidator`` / a ``pre_validate`` for that.
    ``expire_*`` stay on ``ExpiryValidator``, not here.
    """

    @staticmethod
    def _is_valid_card_expiry(value: Any) -> bool:
        return isinstance(value, str) and _MMYY.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_card_expiry(value):
            raise ValueError(f"{self.name} is not a valid card expiry (MMYY)")
