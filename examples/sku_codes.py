# SPDX-License-Identifier: MIT
"""Catalog SKU, hex tint, and slug on the Pattern algebra.

``PatternValidator`` / ``StringValidator(pattern=)`` match with ``re.findall``
(substring), not ``fullmatch``. ``StartsWith`` / ``EndsWith`` make an identity
SKU. ``SetOf`` is the character class (``~SetOf(...)`` negates). Stdlib atoms
``Digit`` / ``Word`` / ``NonWhiteSpace`` share the count-kwargs door. Names
match valio@3415c03; they are the taught field default PatternTypes.
"""

from dataclasses import dataclass

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


@dataclass
class CatalogPart:
    sku: str = StringValidator(pattern=sku_token, required=True)
    tint: str = StringValidator(pattern=hex_pair, required=True)
    slug: str = StringValidator(pattern=slug_token, required=True)
    lot: str = StringValidator(pattern=lot_token, required=True)


def add_part(sku: str, tint: str, slug: str, lot: str) -> CatalogPart:
    """Accept a catalog row. Shape failures raise ``ValueError``."""
    return CatalogPart(sku=sku, tint=tint, slug=slug, lot=lot)


def main() -> CatalogPart:
    part = add_part(sku="INV-0042Z", tint="aF", slug="widget", lot="A1-9")
    try:
        add_part(sku="xINV-0042Z", tint="aF", slug="widget", lot="A1-9")
    except ValueError:
        pass
    try:
        add_part(sku="INV-0042Z", tint="zz", slug="widget", lot="A1-9")
    except ValueError:
        pass
    try:
        add_part(sku="INV-0042Z", tint="aF", slug="ab", lot="A1-9")
    except ValueError:
        pass
    try:
        add_part(sku="INV-0042Z", tint="aF", slug="widget", lot="A 9")
    except ValueError:
        pass
    return part


if __name__ == "__main__":
    stored = main()
    print(f"{stored.sku} tint={stored.tint} slug={stored.slug}")
