# SPDX-License-Identifier: MIT
"""Warehouse line: lookaround units + stock reserve.

Lookarounds are valio@3415c03 PatternTypes. Matching is ``findall``
substring (KEEP). Inject ``Warehouse`` on ``ShippingService``.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    Digit,
    EndsWith,
    IfFollowedBy,
    IfNotFollowedBy,
    IfPrecededBy,
    Pattern,
    StartsWith,
    StringValidator,
)

mass_kg = (
    StartsWith(Digit(count_min=1))
    & IfFollowedBy(Pattern(r"kg"))
    & EndsWith(Pattern(r"kg"))
)
usd_amount = IfPrecededBy(Pattern(r"USD")) & Digit(count_min=1)
not_pounds = Digit(count_min=1) & IfNotFollowedBy(Pattern(r"lb"))


class Warehouse(Protocol):
    """Stock check + reserve. Production: ``UPDATE sku SET qty = qty - 1 WHERE qty >= 1``."""

    def ensure_available(self, sku: str) -> None:
        """Raise ``ValueError`` when the line cannot be reserved."""
        ...

    def reserve(self, sku: str) -> None:
        """Decrement after a successful set."""
        ...


class InMemoryWarehouse:
    """Runnable fake. Plug in a stock row that satisfies ``Warehouse``."""

    def __init__(self, stock: dict[str, int] | None = None) -> None:
        self._stock = dict(stock or {})

    def ensure_available(self, sku: str) -> None:
        if self._stock.get(sku, 0) < 1:
            raise ValueError(f"sku {sku!r} is not in stock")

    def reserve(self, sku: str) -> None:
        self.ensure_available(sku)
        self._stock[sku] -= 1


@dataclass
class Shipment:
    warehouse: Warehouse
    sku: str = StringValidator(min_length=1, required=True)
    mass: str = StringValidator(pattern=mass_kg, required=True)
    price: str = StringValidator(pattern=usd_amount, required=True)
    quantity: str = StringValidator(pattern=not_pounds, required=True)

    @sku.pre_validate
    def in_stock(self, value: str) -> str:
        self.warehouse.ensure_available(value)
        return value

    @sku.post_set
    def reserve_sku(self, value: str) -> None:
        self.warehouse.reserve(value)


class ShippingService:
    """Composition root. Production: ``ShippingService(SqlWarehouse(pool))``."""

    def __init__(self, warehouse: Warehouse) -> None:
        self.warehouse = warehouse

    def book(self, sku: str, mass: str, price: str, quantity: str) -> Shipment:
        return Shipment(
            warehouse=self.warehouse,
            sku=sku,
            mass=mass,
            price=price,
            quantity=quantity,
        )


def main() -> Shipment:
    empty = ShippingService(InMemoryWarehouse(stock={"WIDGET": 0}))
    row = ShippingService(InMemoryWarehouse(stock={"WIDGET": 2})).book(
        sku="WIDGET", mass="12kg", price="USD40", quantity="8"
    )
    try:
        empty.book(sku="WIDGET", mass="12kg", price="USD40", quantity="8")
    except ValueError:
        pass
    try:
        ShippingService(InMemoryWarehouse(stock={"WIDGET": 1})).book(
            sku="WIDGET", mass="12lb", price="USD40", quantity="8"
        )
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    booked = main()
    print(f"{booked.sku} {booked.mass} at {booked.price}")
