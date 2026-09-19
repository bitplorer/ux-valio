# SPDX-License-Identifier: MIT
"""Named identity facades, grouped by where they are used.

Sibling domain modules (parallel, do not import each other)::

    india    — KYC / tax / bank / GST  (Aadhaar, PAN, GSTIN, …)
    finance  — money / cards / ISO currency (IBAN, BIC, PaymentCard, …)
    catalog  — goods (ISBN, EAN, GTIN, VIN)
    contact  — how to reach (Email, Phone, URL, Hostname)
    device   — hardware (IMEI, MAC)
    portal   — SaaS tenancy / i18n (Slug, Country, Timezone, ULID)
    expiry   — wall-clock ``ExpiryValidator`` (not a string identity)

The taught usage is the field default — same shape as every other
validator in this library::

    gstin: str = GSTINValidator()
    isbn: str = ISBNValidator()

Every named facade:

- subclasses ``StringValidator`` (``ExpiryValidator`` is the exception:
  it gates wall-clock on whatever the field stores, so it is ``Validator``)
- strips print grouping in ``_pre_validate`` and **stores the compact
  identity** (uppercase / digits-only as the scheme requires)
- runs its extra from ``validate()`` via ``_validate_named_facade`` —
  it does **not** hang ``@field.validator`` on each assignment
- ``None`` skips (optional field / ``default=None``)
- fail-closed ``ValueError``; format-without-checksum is rejected when
  the scheme has a check digit
- stdlib only, **no portal / network**. ``PhoneNumberValidator`` uses
  the optional ``phonenumbers`` extra and still does no carrier lookup.

They import ``ux_valio.facades.typed`` or the validate door — never each
other, and ``typed`` never imports this package. Public names re-export
from ``ux_valio``; domain imports are for source navigation
(``from ux_valio.facades.named.india import GSTINValidator``).
"""

from ux_valio.facades.named.catalog import (
    EANValidator,
    GTINValidator,
    ISBNValidator,
    VINValidator,
)
from ux_valio.facades.named.contact import (
    EmailValidator,
    HostnameValidator,
    PhoneNumberValidator,
    URLValidator,
)
from ux_valio.facades.named.device import IMEIValidator, MACAddressValidator
from ux_valio.facades.named.expiry import ExpiryValidator
from ux_valio.facades.named.finance import (
    ABARoutingValidator,
    BICValidator,
    CardExpiryValidator,
    CurrencyCodeValidator,
    IBANValidator,
    ISINValidator,
    LEIValidator,
    PaymentCardValidator,
)
from ux_valio.facades.named.india import (
    AadhaarCardValidator,
    CINValidator,
    GSTINValidator,
    HSNCodeValidator,
    IFSCValidator,
    PANCardValidator,
    PinCodeValidator,
    TANValidator,
    UPIIdValidator,
    UdyamValidator,
    VoterIdValidator,
)
from ux_valio.facades.named.portal import (
    CountryCodeValidator,
    SlugValidator,
    TimezoneValidator,
    ULIDValidator,
)

__all__ = [
    "ABARoutingValidator",
    "AadhaarCardValidator",
    "BICValidator",
    "CINValidator",
    "CardExpiryValidator",
    "CountryCodeValidator",
    "CurrencyCodeValidator",
    "EANValidator",
    "EmailValidator",
    "ExpiryValidator",
    "GSTINValidator",
    "GTINValidator",
    "HSNCodeValidator",
    "HostnameValidator",
    "IBANValidator",
    "IFSCValidator",
    "IMEIValidator",
    "ISBNValidator",
    "ISINValidator",
    "LEIValidator",
    "MACAddressValidator",
    "PANCardValidator",
    "PaymentCardValidator",
    "PhoneNumberValidator",
    "PinCodeValidator",
    "SlugValidator",
    "TANValidator",
    "TimezoneValidator",
    "ULIDValidator",
    "UPIIdValidator",
    "UdyamValidator",
    "URLValidator",
    "VINValidator",
    "VoterIdValidator",
]
