# SPDX-License-Identifier: MIT
"""Lookaround PatternTypes on Door A fields (findall substring KEEP)."""

from dataclasses import dataclass

from ux_valio import Digit, IfFollowedBy, IfPrecededBy, Pattern, StringValidator

mass = Digit(count_min=1) & IfFollowedBy(Pattern(r"kg"))
amount = IfPrecededBy(Pattern(r"USD")) & Digit(count_min=1)


@dataclass
class Shipment:
    mass: str = StringValidator(pattern=mass, debug=True, required=True)
    price: str = StringValidator(pattern=amount, debug=True, required=True)


def main() -> Shipment:
    row = Shipment(mass="12kg", price="USD40")
    assert row.mass == "12kg"
    return row


if __name__ == "__main__":
    print(main())
