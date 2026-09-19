# SPDX-License-Identifier: MIT
"""Catalog SKU intake: Pattern algebra + SKU uniqueness.

``PatternValidator`` / ``StringValidator(pattern=)`` match with ``re.findall``
(substring), not ``fullmatch``. ``StartsWith`` / ``EndsWith`` make an identity
SKU. Names match valio@3415c03. Inject ``PartCatalog`` on ``CatalogService``.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    Digit,
    EndsWith,
    NonWhiteSpace,
    Pattern,
    SetOf,
    StartsWith,
    StringValidator,
    Word,
)

sku_token = StartsWith(Pattern(r"INV-")) & Digit(count=4) & EndsWith(Pattern(r"Z"))
hex_pair = SetOf(Pattern(r"0-9a-fA-F"), count=2)
slug_token = Word(count_min=3)
lot_token = NonWhiteSpace(count_min=4)


class PartCatalog(Protocol):
    """SKU uniqueness. Production: unique index on ``sku``."""

    def sku_taken(self, sku: str) -> bool:
        """True when this SKU is already in the catalog."""
        ...

    def commit(self, sku: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryPartCatalog:
    """Runnable fake. Plug in SQL that satisfies ``PartCatalog``."""

    def __init__(self, skus: set[str] | None = None) -> None:
        self._skus = set(skus or ())

    def sku_taken(self, sku: str) -> bool:
        return sku in self._skus

    def commit(self, sku: str) -> None:
        self._skus.add(sku)


@dataclass
class CatalogPart:
    catalog: PartCatalog
    sku: str = StringValidator(pattern=sku_token, required=True)
    tint: str = StringValidator(pattern=hex_pair, required=True)
    slug: str = StringValidator(pattern=slug_token, required=True)
    lot: str = StringValidator(pattern=lot_token, required=True)

    @sku.pre_validate
    def sku_available(self, value: str) -> str:
        if self.catalog.sku_taken(value):
            raise ValueError(f"SKU {value!r} is already catalogued")
        return value

    @sku.post_set
    def commit_sku(self, value: str) -> None:
        self.catalog.commit(value)


class CatalogService:
    """Composition root. Production: ``CatalogService(SqlPartCatalog(pool))``."""

    def __init__(self, catalog: PartCatalog) -> None:
        self.catalog = catalog

    def add(self, sku: str, tint: str, slug: str, lot: str) -> CatalogPart:
        return CatalogPart(
            catalog=self.catalog, sku=sku, tint=tint, slug=slug, lot=lot
        )


def main() -> CatalogPart:
    taken = CatalogService(InMemoryPartCatalog(skus={"INV-0042Z"}))
    part = CatalogService(InMemoryPartCatalog()).add(
        sku="INV-0042Z", tint="aF", slug="widget", lot="A1-9"
    )
    try:
        taken.add(sku="INV-0042Z", tint="aF", slug="widget", lot="A1-9")
    except ValueError:
        pass
    try:
        CatalogService(InMemoryPartCatalog()).add(
            sku="xINV-0042Z", tint="aF", slug="widget", lot="A1-9"
        )
    except ValueError:
        pass
    return part


if __name__ == "__main__":
    stored = main()
    print(f"{stored.sku} tint={stored.tint} slug={stored.slug}")
