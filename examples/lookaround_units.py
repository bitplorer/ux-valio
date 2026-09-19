# SPDX-License-Identifier: MIT
"""Warehouse line: digits only when followed by ``kg`` or preceded by ``USD``.

Lookarounds are valio@3415c03 PatternTypes: ``IfPrecededBy`` /
``IfNotPrecededBy`` / ``IfFollowedBy`` / ``IfNotFollowedBy``. Matching is
``findall`` substring (KEEP). Pair with ``StartsWith`` / ``EndsWith`` when
the assignment must be the whole string.
"""

from dataclasses import dataclass

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

# Identity mass: digits at start, ``kg`` at end, ``kg`` as zero-width lookahead.
mass_kg = (
    StartsWith(Digit(count_min=1))
    & IfFollowedBy(Pattern(r"kg"))
    & EndsWith(Pattern(r"kg"))
)
# Lookbehind cannot sit after ``^``. ``(?<=USD)\d+`` is findall substring (KEEP).
usd_amount = IfPrecededBy(Pattern(r"USD")) & Digit(count_min=1)
not_pounds = Digit(count_min=1) & IfNotFollowedBy(Pattern(r"lb"))


@dataclass
class Shipment:
    mass: str = StringValidator(pattern=mass_kg, required=True)
    price: str = StringValidator(pattern=usd_amount, required=True)
    quantity: str = StringValidator(pattern=not_pounds, required=True)


def book_shipment(mass: str, price: str, quantity: str) -> Shipment:
    """Book a shipment line. Unit or currency mismatches raise."""
    return Shipment(mass=mass, price=price, quantity=quantity)


def main() -> Shipment:
    row = book_shipment(mass="12kg", price="USD40", quantity="8")
    try:
        book_shipment(mass="12lb", price="USD40", quantity="8")
    except ValueError:
        pass
    try:
        book_shipment(mass="12kg", price="EUR40", quantity="8")
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    booked = main()
    print(f"{booked.mass} at {booked.price}")
