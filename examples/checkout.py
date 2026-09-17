# SPDX-License-Identifier: MIT
"""Paid checkout: card brand ∩ Luhn, card month/year pattern, amount, promo window.

``ExpiryValidator`` is a timeline on *now* (offer / hold window), not card
``MM/YY``. Card expiry uses ``StartsWith`` / ``EndsWith`` so findall is an
identity match. ``PaymentCardValidator`` rejects a Luhn-valid non-brand number.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from ux_valio import (
    DecimalValidator,
    Digit,
    EndsWith,
    ExpiryValidator,
    Pattern,
    PaymentCardValidator,
    StartsWith,
    StringValidator,
)

_CARD_EXPIRY = StartsWith(Digit(count=2)) & Pattern(r"/") & EndsWith(Digit(count=2))
_PROMO_UNTIL = (date.today() + timedelta(days=30)).isoformat()
_PROMO_ENDED = (date.today() - timedelta(days=1)).isoformat()


@dataclass
class Checkout:
    holder: str = StringValidator(
        debug=True, required=True, min_length=2, max_length=80
    )
    number: str = PaymentCardValidator(debug=True, required=True)
    card_expiry: str = StringValidator(
        pattern=_CARD_EXPIRY, debug=True, required=True
    )
    amount: Decimal = DecimalValidator(
        min_value=Decimal("0.01"), debug=True, required=True
    )
    promo_code: str = ExpiryValidator(
        expire_after=_PROMO_UNTIL, debug=True, required=True
    )


@dataclass
class ExpiredHold:
    """Offer whose ``expire_after`` bound is already in the past."""

    promo_code: str = ExpiryValidator(
        expire_after=_PROMO_ENDED, debug=True, required=True
    )


def place_order(
    holder: str,
    number: str,
    card_expiry: str,
    amount: Decimal,
    promo_code: str,
) -> Checkout:
    """Place a validated order. Invalid card, amount, or window raise."""
    return Checkout(
        holder=holder,
        number=number,
        card_expiry=card_expiry,
        amount=amount,
        promo_code=promo_code,
    )


def main() -> Checkout:
    order = place_order(
        holder="Ada Lovelace",
        number="4111111111111111",
        card_expiry="12/28",
        amount=Decimal("19.99"),
        promo_code="SPRING30",
    )
    try:
        place_order(
            holder="Ada Lovelace",
            number="4111111111111112",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
        )
    except ValueError:
        pass
    try:
        ExpiredHold(promo_code="LATE")
    except ValueError:
        pass
    return order


if __name__ == "__main__":
    placed = main()
    print(f"{placed.holder} charged {placed.amount} on {placed.number[-4:]}")
