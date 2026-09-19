# SPDX-License-Identifier: MIT
"""Paid checkout: card brand ∩ Luhn, card MM/YY, promo lookup, stock, gateway.

``ExpiryValidator`` is a timeline on *now* (offer / hold window), not card
``MM/YY``. Card print form is ``CardExpiryValidator``.

Ports fail closed into validation errors via ``post_validate`` (after
the field’s own identity). Persist/reserve on ``post_set``:

* ``PromoCatalog.lookup`` — unknown code
* ``Inventory.ensure_available`` / ``reserve`` — stock
* ``PaymentGateway.authorize`` — decline

Inject the ports on ``CheckoutService``; ``main()`` only runs the demo.
In-memory fakes keep it offline. Production plugs an offers table, a stock
row (or Redis), and Stripe/Razorpay. This file does not ship a DB driver.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol, runtime_checkable

from ux_valio import (
    CardExpiryValidator,
    DecimalValidator,
    ExpiryValidator,
    IntegerValidator,
    PaymentCardValidator,
    StringValidator,
    Validator,
)

_PROMO_UNTIL = (date.today() + timedelta(days=30)).isoformat()
_PROMO_ENDED = (date.today() - timedelta(days=1)).isoformat()


@runtime_checkable
class PromoCatalog(Protocol):
    """Offer lookup. Production: ``SELECT code FROM offers WHERE code=$1``."""

    def lookup(self, code: str) -> str:
        """Return the canonical code, or raise ``ValueError`` if unknown."""
        ...


@runtime_checkable
class Inventory(Protocol):
    """Stock check + reserve. Production: ``UPDATE sku SET qty = qty - $1 WHERE qty >= $1``."""

    def ensure_available(self, sku: str, quantity: int) -> None:
        """Raise ``ValueError`` when stock cannot cover ``quantity``."""
        ...

    def reserve(self, sku: str, quantity: int) -> None:
        """Commit the hold after a successful set."""
        ...


@runtime_checkable
class PaymentGateway(Protocol):
    """Authorize (no capture). Production: Stripe/Razorpay SDK; map decline → ``ValueError``."""

    def authorize(self, number: str, amount: Decimal) -> str:
        """Return an auth id, or raise ``ValueError`` on decline."""
        ...


class InMemoryPromoCatalog:
    """Runnable fake. Plug in an offers table that satisfies ``PromoCatalog``."""

    def __init__(self, codes: set[str] | None = None) -> None:
        self.codes = {code.upper(): code for code in (codes or set())}

    def lookup(self, code: str) -> str:
        found = self.codes.get(code.upper())
        if found is None:
            raise ValueError(f"unknown promo {code!r}")
        return found


class InMemoryInventory:
    """Runnable fake. Plug in SQL/Redis stock that satisfies ``Inventory``."""

    def __init__(self, stock: dict[str, int] | None = None) -> None:
        self.stock = dict(stock or {})

    def ensure_available(self, sku: str, quantity: int) -> None:
        have = self.stock.get(sku, 0)
        if have < quantity:
            raise ValueError(f"sku {sku!r} has {have} in stock, need {quantity}")

    def reserve(self, sku: str, quantity: int) -> None:
        self.ensure_available(sku, quantity)
        self.stock[sku] = self.stock.get(sku, 0) - quantity


class StubPaymentGateway:
    """Runnable fake. Plug in Stripe/Razorpay that satisfies ``PaymentGateway``."""

    def __init__(self, declines: set[str] | None = None) -> None:
        self.declines = set(declines or ())

    def authorize(self, number: str, amount: Decimal) -> str:
        if number in self.declines:
            raise ValueError("payment declined")
        return f"auth-{number[-4:]}"


@dataclass
class Checkout:
    promos: PromoCatalog = field(
        default=Validator[PromoCatalog](required=True),
        repr=False,
        compare=False,
    )
    inventory: Inventory = field(
        default=Validator[Inventory](required=True),
        repr=False,
        compare=False,
    )
    gateway: PaymentGateway = field(
        default=Validator[PaymentGateway](required=True),
        repr=False,
        compare=False,
    )
    holder: str = StringValidator(
        required=True, min_length=2, max_length=80
    )
    number: str = PaymentCardValidator(required=True)
    card_expiry: str = CardExpiryValidator(required=True)
    sku: str = StringValidator(required=True, min_length=1, max_length=32)
    amount: Decimal = DecimalValidator(
        min_value=Decimal("0.01"), required=True
    )
    promo_code: str = ExpiryValidator(expire_after=_PROMO_UNTIL, required=True)
    quantity: int = IntegerValidator(min_value=1, required=True)

    @promo_code.post_validate
    def promo_known(self, value: str) -> str:
        return self.promos.lookup(value)

    @quantity.post_validate
    def stock_available(self, value: int) -> int:
        self.inventory.ensure_available(self.sku, value)
        return value

    @quantity.post_validate
    def card_authorized(self, value: int) -> int:
        self.gateway.authorize(self.number, self.amount)
        return value

    @quantity.post_set
    def reserve_stock(self, value: int) -> None:
        self.inventory.reserve(self.sku, value)


@dataclass
class ExpiredHold:
    """Offer whose ``expire_after`` bound is already in the past."""

    promo_code: str = ExpiryValidator(
        expire_after=_PROMO_ENDED, required=True
    )


class CheckoutService:
    """Composition root. Production: SQL offers, stock row, Stripe."""

    def __init__(
        self,
        *,
        promos: PromoCatalog,
        inventory: Inventory,
        gateway: PaymentGateway,
    ) -> None:
        self.promos = promos
        self.inventory = inventory
        self.gateway = gateway

    def place(
        self,
        holder: str,
        number: str,
        card_expiry: str,
        amount: Decimal,
        promo_code: str,
        sku: str = "WIDGET",
        quantity: int = 1,
    ) -> Checkout:
        """Place a validated order. Invalid card, promo, stock, or gateway raise."""
        return Checkout(
            promos=self.promos,
            inventory=self.inventory,
            gateway=self.gateway,
            holder=holder,
            number=number,
            card_expiry=card_expiry,
            sku=sku,
            amount=amount,
            promo_code=promo_code,
            quantity=quantity,
        )


def main() -> Checkout:
    service = CheckoutService(
        promos=InMemoryPromoCatalog(codes={"SPRING30"}),
        inventory=InMemoryInventory(stock={"WIDGET": 10}),
        gateway=StubPaymentGateway(),
    )
    order = service.place(
        holder="Ada Lovelace",
        number="4111111111111111",
        card_expiry="12/28",
        amount=Decimal("19.99"),
        promo_code="SPRING30",
        sku="WIDGET",
        quantity=1,
    )
    try:
        service.place(
            holder="Ada Lovelace",
            number="4111111111111112",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
        )
    except ValueError:
        pass
    try:
        service.place(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="NOPE",
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
