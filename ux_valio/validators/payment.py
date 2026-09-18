# SPDX-License-Identifier: MIT
"""Payment-card Door A facade. Brand ∩ Luhn via stdlib ``re`` (no pyparsing)."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.validators.typed import StringValidator

# IIN literals from valio relib/paymentcards.py comments @ 3415c03.
# Identity match (full string), not PatternValidator findall.
# Rupay live identity is 60 + 14 digits except Discover overlap (6011 / 644x / 65xx).
# The 6521/6522 alternative is dead: lookahead 5[0-9]{2} already rejects it.
_VISA = re.compile(r"4[0-9]{12}(?:[0-9]{3})?")
_MASTERCARD = re.compile(
    r"(?:5[1-5][0-9]{14}|222[1-9][0-9]{12}|22[3-9][0-9]{13}|2[3-6][0-9]{14}|27[01][0-9]{13}|2720[0-9]{12})"
)
_AMEX = re.compile(r"3[47][0-9]{13}")
_DISCOVER = re.compile(r"(?:6011|644[0-9]|65[0-9]{2})[0-9]{12}")
_RUPAY = re.compile(r"6(?!(?:011|44[0-9]|5[0-9]{2}))0[0-9]{14}")


class PaymentCardValidator(StringValidator):
    """Door A string facade: Visa / Mastercard / Amex / Discover / Rupay ∩ Luhn."""

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
        )

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        """Printed cards group digits. Store the compact brand∩Luhn identity."""
        if isinstance(value, str):
            value = "".join(value.split()).replace("-", "")
        return super().pre_validation_processing(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_payment_card(instance, value)

    def _validate_payment_card(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_payment_card(value):
            raise ValueError(f"{self.name} is not a valid payment card number")
