# SPDX-License-Identifier: MIT
"""Payment card number and MM/YY print form.

Sibling of the other ``finance`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.finance``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_VISA = re.compile(r"4[0-9]{12}(?:[0-9]{3})?")
_MASTERCARD = re.compile(
    r"(?:5[1-5][0-9]{14}|222[1-9][0-9]{12}|22[3-9][0-9]{13}|2[3-6][0-9]{14}|27[01][0-9]{13}|2720[0-9]{12})"
)
_AMEX = re.compile(r"3[47][0-9]{13}")
_DISCOVER = re.compile(r"(?:6011|644[0-9]|65[0-9]{2})[0-9]{12}")
_RUPAY = re.compile(r"6(?!(?:011|44[0-9]|5[0-9]{2}))0[0-9]{14}")
_UNIONPAY = re.compile(r"62[0-9]{14,17}")
_JCB = re.compile(r"(?:352[8-9]|35[3-8][0-9])[0-9]{12}")
_DINERS = re.compile(r"3(?:0[0-5]|[68][0-9])[0-9]{11}")


class PaymentCardValidator(StringValidator):
    """Visa / Mastercard / Amex / Discover / Rupay / UnionPay / JCB / Diners ∩ Luhn.

    Usage::

        number: str = PaymentCardValidator()

    Print grouping spaces/hyphens strip; stores compact digits. A
    Luhn-valid non-brand number is rejected. No network / BIN lookup.
    """

    @staticmethod
    def _luhn_correctness(card_number: str) -> bool:
        if not card_number.isdigit():
            return False
        digits = list(card_number)
        digits.reverse()
        total = 0
        odd = True
        for digit in digits:
            n = int(digit)
            if odd := not odd:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    @staticmethod
    def _is_card_of(pattern: re.Pattern[str], card_number: str) -> bool:
        return (
            PaymentCardValidator._luhn_correctness(card_number)
            and pattern.fullmatch(card_number) is not None
        )

    @staticmethod
    def _is_valid_payment_card(card_number: str) -> bool:
        """True only when Luhn holds **and** the number matches a known brand."""
        if not isinstance(card_number, str):
            return False
        is_card = PaymentCardValidator._is_card_of
        return (
            is_card(_VISA, card_number)
            or is_card(_MASTERCARD, card_number)
            or is_card(_AMEX, card_number)
            or is_card(_DISCOVER, card_number)
            or is_card(_RUPAY, card_number)
            or is_card(_UNIONPAY, card_number)
            or is_card(_JCB, card_number)
            or is_card(_DINERS, card_number)
        )

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        """Printed cards group digits. Store the compact brand∩Luhn identity."""
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "")
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_payment_card(instance, value)

    def _validate_payment_card(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_payment_card(value):
            raise ValueError(f"{self.name} is not a valid payment card number")

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
