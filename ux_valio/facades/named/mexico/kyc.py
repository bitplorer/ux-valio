# SPDX-License-Identifier: MIT
"""Mexico tax identity (RFC).

Sibling of the other ``mexico`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.mexico``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator


_ALPH = "0123456789ABCDEFGHIJKLMN&OPQRSTUVWXYZ Ñ"
_PERSON = re.compile(r"[A-Z&Ñ]{4}[0-9]{6}[A-Z0-9]{3}")
_COMPANY = re.compile(r"[A-Z&Ñ]{3}[0-9]{6}[A-Z0-9]{3}")


class MexicoRFCValidator(StringValidator):
    """Mexican RFC: 12 (moral) or 13 (física) ∩ SAT check digit.

    Usage::

        rfc: str = MexicoRFCValidator()

    Spaces/hyphens strip; stores uppercase. Format-only is rejected.
    Named ``MexicoRFCValidator`` so it is not confused with an IETF RFC.
    No SAT lookup.
    """

    @staticmethod
    def _check_digit(body: str) -> str:
        padded = (" " + body)[-12:]
        total = sum(_ALPH.index(char) * (13 - index) for index, char in enumerate(padded))
        return _ALPH[(11 - total) % 11]

    @staticmethod
    def _is_valid_rfc(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        if _PERSON.fullmatch(value) is None and _COMPANY.fullmatch(value) is None:
            return False
        try:
            return MexicoRFCValidator._check_digit(value[:-1]) == value[-1]
        except ValueError:
            return False

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_rfc(value):
            raise ValueError(f"{self.name} is not a valid Mexican RFC")
