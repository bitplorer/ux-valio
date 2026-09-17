# SPDX-License-Identifier: MIT
"""Checkout: payment brand ∩ Luhn, expiry timeline, decimal amount."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from ux_valio import DecimalValidator, ExpiryValidator, PaymentCardValidator, StringValidator

FUTURE = (date.today() + timedelta(days=365)).isoformat()


@dataclass
class Checkout:
    holder: str = StringValidator(debug=True, required=True, min_length=2, max_length=80)
    number: str = PaymentCardValidator(debug=True, required=True)
    until: str = ExpiryValidator(expire_after=FUTURE, debug=True, required=True)
    amount: Decimal = DecimalValidator(min_value=Decimal("0.01"), debug=True, required=True)


def main() -> Checkout:
    order = Checkout(
        holder="Ada Lovelace",
        number="4111111111111111",
        until="ok",
        amount=Decimal("19.99"),
    )
    assert order.number.startswith("4111")
    return order


if __name__ == "__main__":
    print(main())
