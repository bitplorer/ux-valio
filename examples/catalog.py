# SPDX-License-Identifier: MIT
"""Product catalog line: SKU identity, units, stock reserve.

``Pattern`` / ``StringValidator(pattern=)`` match with ``re.findall``
(substring), not ``fullmatch``. ``StartsWith`` / ``EndsWith`` make the SKU.
Lookarounds (``IfFollowedBy`` / ``IfPrecededBy``) pin units. Matching is
findall (KEEP).

Uniqueness hangs on ``post_validate``. Stock ensure is also
``post_validate`` (after identity). Reserve on ``post_set`` of the last
field. Inject ``PartCatalog`` + ``Warehouse`` on ``CatalogService``.
Production: unique index on SKU + ``UPDATE qty WHERE qty >= 1``.
"""

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ux_valio import (
    Digit,
    EndsWith,
    IfFollowedBy,
    IfNotFollowedBy,
    IfPrecededBy,
    NonWhiteSpace,
    Pattern,
    SetOf,
    StartsWith,
    StringValidator,
    Validator,
    Word,
)

sku_token = StartsWith(Pattern(r"INV-")) & Digit(count=4) & EndsWith(Pattern(r"Z"))
hex_pair = SetOf(Pattern(r"0-9a-fA-F"), count=2)
slug_token = Word(count_min=3)
lot_token = NonWhiteSpace(count_min=4)
mass_kg = (
    StartsWith(Digit(count_min=1))
    & IfFollowedBy(Pattern(r"kg"))
    & EndsWith(Pattern(r"kg"))
)
usd_amount = IfPrecededBy(Pattern(r"USD")) & Digit(count_min=1)
not_pounds = Digit(count_min=1) & IfNotFollowedBy(Pattern(r"lb"))


@runtime_checkable
class PartCatalog(Protocol):
    """SKU uniqueness. Production: unique index on ``sku``."""

    def sku_taken(self, sku: str) -> bool:
        """True when this SKU is already in the catalog."""
        ...

    def commit(self, sku: str) -> None:
        """Persist after a successful set."""
        ...


@runtime_checkable
class Warehouse(Protocol):
    """Stock check + reserve. Production: ``UPDATE sku SET qty = qty - 1 WHERE qty >= 1``."""

    def ensure_available(self, sku: str) -> None:
        """Raise ``ValueError`` when the line cannot be reserved."""
        ...

    def reserve(self, sku: str) -> None:
        """Decrement after a successful set."""
        ...


class InMemoryPartCatalog:
    """Runnable fake. Plug in SQL that satisfies ``PartCatalog``."""

    def __init__(self, skus: set[str] | None = None) -> None:
        self._skus = set(skus or ())

    def sku_taken(self, sku: str) -> bool:
        return sku in self._skus

    def commit(self, sku: str) -> None:
        self._skus.add(sku)


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
class CatalogLine:
    catalog: PartCatalog = field(
        default=Validator[PartCatalog](required=True),
        repr=False,
        compare=False,
    )
    warehouse: Warehouse = field(
        default=Validator[Warehouse](required=True),
        repr=False,
        compare=False,
    )
    sku: str = StringValidator(pattern=sku_token, required=True)
    tint: str = StringValidator(pattern=hex_pair, required=True)
    slug: str = StringValidator(pattern=slug_token, required=True)
    lot: str = StringValidator(pattern=lot_token, required=True)
    mass: str = StringValidator(pattern=mass_kg, required=True)
    price: str = StringValidator(pattern=usd_amount, required=True)
    quantity: str = StringValidator(pattern=not_pounds, required=True)

    @sku.post_validate
    def sku_available(self, value: str) -> str:
        if self.catalog.sku_taken(value):
            raise ValueError(f"SKU {value!r} is already catalogued")
        return value

    @quantity.post_validate
    def in_stock(self, value: str) -> str:
        self.warehouse.ensure_available(self.sku)
        return value

    @quantity.post_set
    def commit_and_reserve(self, value: str) -> None:
        self.catalog.commit(self.sku)
        self.warehouse.reserve(self.sku)


class CatalogService:
    """Composition root. Production: SQL unique SKU + stock row."""

    def __init__(self, catalog: PartCatalog, warehouse: Warehouse) -> None:
        self.catalog = catalog
        self.warehouse = warehouse

    def add(
        self,
        sku: str,
        tint: str,
        slug: str,
        lot: str,
        mass: str,
        price: str,
        quantity: str,
    ) -> CatalogLine:
        return CatalogLine(
            catalog=self.catalog,
            warehouse=self.warehouse,
            sku=sku,
            tint=tint,
            slug=slug,
            lot=lot,
            mass=mass,
            price=price,
            quantity=quantity,
        )


def main() -> CatalogLine:
    taken = CatalogService(
        InMemoryPartCatalog(skus={"INV-0042Z"}),
        InMemoryWarehouse(stock={"INV-0042Z": 2}),
    )
    line = CatalogService(
        InMemoryPartCatalog(),
        InMemoryWarehouse(stock={"INV-0042Z": 2}),
    ).add(
        sku="INV-0042Z",
        tint="aF",
        slug="widget",
        lot="A1-9",
        mass="12kg",
        price="USD40",
        quantity="8",
    )
    try:
        taken.add(
            sku="INV-0042Z",
            tint="aF",
            slug="widget",
            lot="A1-9",
            mass="12kg",
            price="USD40",
            quantity="8",
        )
    except ValueError:
        pass
    try:
        CatalogService(
            InMemoryPartCatalog(),
            InMemoryWarehouse(stock={"INV-0042Z": 0}),
        ).add(
            sku="INV-0042Z",
            tint="aF",
            slug="widget",
            lot="A1-9",
            mass="12kg",
            price="USD40",
            quantity="8",
        )
    except ValueError:
        pass
    try:
        CatalogService(
            InMemoryPartCatalog(),
            InMemoryWarehouse(stock={"INV-0042Z": 2}),
        ).add(
            sku="xINV-0042Z",
            tint="aF",
            slug="widget",
            lot="A1-9",
            mass="12kg",
            price="USD40",
            quantity="8",
        )
    except ValueError:
        pass
    return line


if __name__ == "__main__":
    stored = main()
    print(f"{stored.sku} tint={stored.tint} mass={stored.mass}")
