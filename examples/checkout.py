# SPDX-License-Identifier: MIT
"""Paid checkout: card brand ∩ Luhn, card MM/YY, promo lookup, stock, gateway.

``ExpiryValidator`` is a timeline on *now* (offer / hold window), not card
``MM/YY``. Card expiry uses ``StartsWith`` / ``EndsWith`` so findall is an
identity match. ``PaymentCardValidator`` rejects a Luhn-valid non-brand number.

Ports fail closed into validation errors:

* ``PromoCatalog.lookup`` — unknown code
* ``Inventory.ensure_available`` / ``reserve`` — stock
* ``PaymentGateway.authorize`` — decline

In-memory fakes run the demo. Production plugs an offers table, a stock row
(or Redis), and Stripe/Razorpay. This file does not ship a DB driver.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol

from ux_valio import (
    DecimalValidator,
    Digit,
    EndsWith,
    ExpiryValidator,
    IntegerValidator,
    Pattern,
    PaymentCardValidator,
    StartsWith,
    StringValidator,
)

_CARD_EXPIRY = StartsWith(Digit(count=2)) & Pattern(r"/") & EndsWith(Digit(count=2))
_PROMO_UNTIL = (date.today() + timedelta(days=30)).isoformat()
_PROMO_ENDED = (date.today() - timedelta(days=1)).isoformat()


class PromoCatalog(Protocol):
    """Offer lookup. Production: ``SELECT code FROM offers WHERE code=$1``."""

    def lookup(self, code: str) -> str:
        """Return the canonical code, or raise ``ValueError`` if unknown."""
        ...


class Inventory(Protocol):
    """Stock check + reserve. Production: ``UPDATE sku SET qty = qty - $1 WHERE qty >= $1``."""

    def ensure_available(self, sku: str, quantity: int) -> None:
        """Raise ``ValueError`` when stock cannot cover ``quantity``."""
        ...

    def reserve(self, sku: str, quantity: int) -> None:
        """Commit the hold after a successful set."""
        ...


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


PROMOS: PromoCatalog = InMemoryPromoCatalog(codes={"SPRING30"})
INVENTORY: Inventory = InMemoryInventory(stock={"WIDGET": 10})
GATEWAY: PaymentGateway = StubPaymentGateway()

sku_field = StringValidator(debug=True, required=True, min_length=1, max_length=32)
amount_field = DecimalValidator(min_value=Decimal("0.01"), debug=True, required=True)
promo_field = ExpiryValidator(expire_after=_PROMO_UNTIL, debug=True, required=True)
quantity_field = IntegerValidator(min_value=1, debug=True, required=True)


@dataclass
class Checkout:
    holder: str = StringValidator(
        debug=True, required=True, min_length=2, max_length=80
    )
    number: str = PaymentCardValidator(debug=True, required=True)
    card_expiry: str = StringValidator(
        pattern=_CARD_EXPIRY, debug=True, required=True
    )
    sku: str = sku_field
    amount: Decimal = amount_field
    promo_code: str = promo_field
    quantity: int = quantity_field

    @promo_field.add_pre_validator
    def promo_known(self, value: str) -> str:
        return PROMOS.lookup(value)

    @quantity_field.add_pre_validator
    def stock_available(self, value: int) -> int:
        INVENTORY.ensure_available(self.sku, value)
        return value

    @quantity_field.add_validator
    def card_authorized(self, value: int) -> None:
        GATEWAY.authorize(self.number, self.amount)

    @quantity_field.add_post_set
    def reserve_stock(self, value: int) -> None:
        INVENTORY.reserve(self.sku, value)


@dataclass
class ExpiredHold:
    """Offer whose ``expire_after`` bound is already in the past."""

    promo_code: str = ExpiryValidator(
        expire_after=_PROMO_ENDED, debug=True, required=True
    )


def bind_checkout(
    *,
    promos: PromoCatalog | None = None,
    inventory: Inventory | None = None,
    gateway: PaymentGateway | None = None,
) -> None:
    """Process composition root. Production: SQL offers, stock row, Stripe."""
    global PROMOS, INVENTORY, GATEWAY
    if promos is not None:
        PROMOS = promos
    if inventory is not None:
        INVENTORY = inventory
    if gateway is not None:
        GATEWAY = gateway


def place_order(
    holder: str,
    number: str,
    card_expiry: str,
    amount: Decimal,
    promo_code: str,
    sku: str = "WIDGET",
    quantity: int = 1,
    *,
    promos: PromoCatalog | None = None,
    inventory: Inventory | None = None,
    gateway: PaymentGateway | None = None,
) -> Checkout:
    """Place a validated order. Invalid card, promo, stock, or gateway raise."""
    bind_checkout(promos=promos, inventory=inventory, gateway=gateway)
    return Checkout(
        holder=holder,
        number=number,
        card_expiry=card_expiry,
        sku=sku,
        amount=amount,
        promo_code=promo_code,
        quantity=quantity,
    )


def main() -> Checkout:
    promos = InMemoryPromoCatalog(codes={"SPRING30"})
    inventory = InMemoryInventory(stock={"WIDGET": 10})
    gateway = StubPaymentGateway()
    order = place_order(
        holder="Ada Lovelace",
        number="4111111111111111",
        card_expiry="12/28",
        amount=Decimal("19.99"),
        promo_code="SPRING30",
        sku="WIDGET",
        quantity=1,
        promos=promos,
        inventory=inventory,
        gateway=gateway,
    )
    try:
        place_order(
            holder="Ada Lovelace",
            number="4111111111111112",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
            promos=promos,
            inventory=InMemoryInventory(stock={"WIDGET": 10}),
            gateway=gateway,
        )
    except ValueError:
        pass
    try:
        place_order(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="NOPE",
            promos=promos,
            inventory=InMemoryInventory(stock={"WIDGET": 10}),
            gateway=gateway,
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
