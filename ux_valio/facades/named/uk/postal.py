# SPDX-License-Identifier: MIT
"""UK postal identity (Royal Mail postcode).

Sibling of the other ``uk`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.uk``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_UK = re.compile(
    r"(?:GIR 0AA|[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2})"
)

class UKPostcodeValidator(StringValidator):
    """UK postcode (Royal Mail outward + inward).

    Usage::

        postcode: str = UKPostcodeValidator()

    Stores uppercase with one space (``SW1A 1AA``). No Royal Mail lookup.
    """

    @staticmethod
    def _is_valid_uk_postcode(value: Any) -> bool:
        return isinstance(value, str) and _UK.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            compact = "".join(value.split()).upper()
            if len(compact) >= 5:
                value = f"{compact[:-3]} {compact[-3:]}"
            else:
                value = compact
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_uk_postcode(value):
            raise ValueError(f"{self.name} is not a valid UK postcode")

