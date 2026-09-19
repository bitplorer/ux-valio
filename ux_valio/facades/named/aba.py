# SPDX-License-Identifier: MIT
"""ABA routing number. 9 digits ∩ ABA checksum. No Fed directory."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator

_WEIGHTS = (3, 7, 1, 3, 7, 1, 3, 7, 1)


class ABARoutingValidator(StringValidator):
    """US ABA routing number. Complements ``IFSCValidator``.

    Usage::

        routing: str = ABARoutingValidator()

    Non-digits strip; stores 9 digits. Format-only is rejected. No Fed
    directory lookup.
    """

    @staticmethod
    def _is_valid_aba(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 9 or not value.isdigit():
            return False
        total = sum(int(char) * weight for char, weight in zip(value, _WEIGHTS))
        return total % 10 == 0

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_aba(value):
            raise ValueError(f"{self.name} is not a valid ABA routing number")
