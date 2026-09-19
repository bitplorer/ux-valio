# SPDX-License-Identifier: MIT
"""UK bank rail (sort code).

Sibling of the other ``uk`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.uk``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_SORT = re.compile(r"[0-9]{6}")


class UKSortCodeValidator(StringValidator):
    """UK sort code: 6 digits. Complements ABA / IFSC.

    Usage::

        sort: str = UKSortCodeValidator()

    Accepts ``12-34-56``; stores ``123456``. No bank-directory check.
    """

    @staticmethod
    def _is_valid_sort_code(value: Any) -> bool:
        return isinstance(value, str) and _SORT.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_sort_code(value):
            raise ValueError(f"{self.name} is not a valid UK sort code")

