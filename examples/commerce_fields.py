# SPDX-License-Identifier: MIT
"""E-commerce / SaaS identity fields as dataclass defaults.

Copy the dataclass. Uniqueness (SKU, tenant host) stays in a port —
these facades only prove the identity string.
"""

from dataclasses import dataclass

from ux_valio import (
    ABARoutingValidator,
    CardExpiryValidator,
    CountryCodeValidator,
    CurrencyCodeValidator,
    GTINValidator,
    HSNCodeValidator,
    HostnameValidator,
    LEIValidator,
    SlugValidator,
    TimezoneValidator,
    ULIDValidator,
)


@dataclass
class Storefront:
    public_id: str = ULIDValidator()
    host: str = HostnameValidator()
    slug: str = SlugValidator()
    gtin: str = GTINValidator()
    hsn: str = HSNCodeValidator()
    currency: str = CurrencyCodeValidator()
    country: str = CountryCodeValidator()
    tz: str = TimezoneValidator()
    exp: str = CardExpiryValidator()
    routing: str = ABARoutingValidator()
    lei: str = LEIValidator()


def main() -> None:
    row = Storefront(
        public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        host="API.Example.COM.",
        slug="Hello-World",
        gtin="036000291452",
        hsn="87032110",
        currency="inr",
        country="in",
        tz="Asia/Kolkata",
        exp="12/25",
        routing="021000021",
        lei="5493001KJTIIGC8Y1R12",
    )
    print(row.host, row.slug, row.currency, row.exp)


if __name__ == "__main__":
    main()
