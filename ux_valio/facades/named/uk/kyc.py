# SPDX-License-Identifier: MIT
"""UK person KYC (NINO).

Sibling of the other ``uk`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.uk``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_NINO = re.compile(
    r"(?!BG|GB|KN|NK|NT|TN|ZZ)"
    r"[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z][0-9]{6}[A-D]"
)


class NINOValidator(StringValidator):
    """UK National Insurance number.

    Usage::

        nino: str = NINOValidator()

    ``AB 12 34 56 C`` → ``AB123456C``. Prefix letters follow HMRC
    NIM39110; suffix ``A``–``D``. No HMRC lookup.
    """

    @staticmethod
    def _is_valid_nino(value: Any) -> bool:
        return isinstance(value, str) and _NINO.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_nino(value):
            raise ValueError(f"{self.name} is not a valid NINO")
