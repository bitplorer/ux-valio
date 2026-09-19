# SPDX-License-Identifier: MIT
"""Bank rails (IBAN, BIC, ABA).

Sibling of the other ``finance`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.finance``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_IBAN = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")


class IBANValidator(StringValidator):
    """IBAN: ISO 13616, length 15–34 ∩ rearrange-and-mod-97 == 1.

    Usage::

        iban: str = IBANValidator()

    Print groups (``GB82 WEST …``) strip; stores uppercase compact.
    Format-only is rejected. No bank lookup. Pair with ``BICValidator``.
    """

    @staticmethod
    def _mod97(text: str) -> bool:
        rearranged = text[4:] + text[:4]
        digits = "".join(
            str(ord(char) - 55) if char.isalpha() else char for char in rearranged
        )
        return int(digits) % 97 == 1

    @staticmethod
    def _is_valid_iban(value: Any) -> bool:
        if not isinstance(value, str) or not (15 <= len(value) <= 34):
            return False
        if _IBAN.fullmatch(value) is None:
            return False
        return IBANValidator._mod97(value)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_iban(value):
            raise ValueError(f"{self.name} is not a valid IBAN")

_BIC = re.compile(r"[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?")


class BICValidator(StringValidator):
    """SWIFT/BIC bank identifier (ISO 9362).

    Usage::

        swift: str = BICValidator()

    8 characters (``DEUTDEFF``) or 11 (``DEUTDEFF500``). Spaces/hyphens
    strip; stores uppercase. No SWIFT directory. Pair with ``IBANValidator``.
    """

    @staticmethod
    def _is_valid_bic(value: Any) -> bool:
        return isinstance(value, str) and _BIC.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "").upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_bic(value):
            raise ValueError(f"{self.name} is not a valid BIC")

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


_CLABE_WEIGHTS = (3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7)


class CLABEValidator(StringValidator):
    """Mexico CLABE: 18 digits ∩ Banxico check. Complements IBAN.

    Usage::

        clabe: str = CLABEValidator()

    Non-digits strip; stores 18 digits. Format-only is rejected. No
    SPEI directory.
    """

    @staticmethod
    def _is_valid_clabe(value: Any) -> bool:
        if not isinstance(value, str) or len(value) != 18 or not value.isdigit():
            return False
        total = sum(
            int(char) * weight for char, weight in zip(value[:17], _CLABE_WEIGHTS)
        )
        return str((10 - total % 10) % 10) == value[17]

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_clabe(value):
            raise ValueError(f"{self.name} is not a valid CLABE")


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
