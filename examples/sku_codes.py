# SPDX-License-Identifier: MIT
"""SKU and hex codes: StartsWith / EndsWith / SetOf / Digit on Door A."""

from dataclasses import dataclass

from ux_valio import Digit, Pattern, PatternValidator, SetOf, StartsWith, EndsWith, Word


sku = StartsWith(Pattern(r"INV-")) & Digit(count=4) & EndsWith(Pattern(r"Z"))
hex_pair = SetOf(Pattern(r"0-9a-fA-F"), count=2)
token = Word(count_min=3)


@dataclass
class CatalogPart:
    sku: str = PatternValidator(pattern=sku, debug=True, required=True)
    tint: str = PatternValidator(pattern=hex_pair, debug=True, required=True)
    slug: str = PatternValidator(pattern=token, debug=True, required=True)


def main() -> CatalogPart:
    part = CatalogPart(sku="INV-0042Z", tint="aF", slug="widget")
    assert part.sku == "INV-0042Z"
    return part


if __name__ == "__main__":
    print(main())
