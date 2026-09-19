# SPDX-License-Identifier: MIT
"""Named identity facades, grouped by where they are used.

Sibling domain modules (parallel, do not import each other)::

    india/    — KYC / GST / registry / bank  (folder of layers)
    finance/  — rails / market / card / ISO currency (folder of layers)
    catalog  — goods (ISBN, ISSN, EAN, GTIN, VIN)
    address  — US ZIP / CA / UK postcode
    contact  — how to reach (Email, Phone, URL, Hostname)
    device   — hardware (IMEI, MAC)
    portal   — SaaS (Slug, Country, Timezone, ULID, Locale, SemVer)
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
(``from ux_valio.facades.named.india.gst import GSTINValidator``).
"""

from ux_valio.facades.named.address import (
    CAPostalCodeValidator,
    UKPostcodeValidator,
    USZipCodeValidator,
)
from ux_valio.facades.named.catalog import (
    EANValidator,
    GTINValidator,
    ISBNValidator,
    ISSNValidator,
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
    CLABEValidator,
    CUSIPValidator,
    CardExpiryValidator,
    CurrencyCodeValidator,
    IBANValidator,
    ISINValidator,
    LEIValidator,
    PaymentCardValidator,
    UKSortCodeValidator,
)
from ux_valio.facades.named.india import (
    AadhaarCardValidator,
    CINValidator,
    DINValidator,
    FSSAIValidator,
    GSTINValidator,
    HSNCodeValidator,
    IFSCValidator,
    IndianPassportValidator,
    LLPINValidator,
    PANCardValidator,
    PinCodeValidator,
    TANValidator,
    UPIIdValidator,
    UdyamValidator,
    VoterIdValidator,
)
from ux_valio.facades.named.portal import (
    CountryCodeValidator,
    LocaleValidator,
    SemVerValidator,
    SlugValidator,
    TimezoneValidator,
    ULIDValidator,
)

__all__ = [
    "ABARoutingValidator",
    "AadhaarCardValidator",
    "BICValidator",
    "CAPostalCodeValidator",
    "CINValidator",
    "CLABEValidator",
    "CUSIPValidator",
    "CardExpiryValidator",
    "CountryCodeValidator",
    "CurrencyCodeValidator",
    "DINValidator",
    "EANValidator",
    "EmailValidator",
    "ExpiryValidator",
    "FSSAIValidator",
    "GSTINValidator",
    "GTINValidator",
    "HSNCodeValidator",
    "HostnameValidator",
    "IBANValidator",
    "IFSCValidator",
    "IMEIValidator",
    "ISBNValidator",
    "ISINValidator",
    "ISSNValidator",
    "IndianPassportValidator",
    "LEIValidator",
    "LLPINValidator",
    "LocaleValidator",
    "MACAddressValidator",
    "PANCardValidator",
    "PaymentCardValidator",
    "PhoneNumberValidator",
    "PinCodeValidator",
    "SemVerValidator",
    "SlugValidator",
    "TANValidator",
    "TimezoneValidator",
    "UKPostcodeValidator",
    "UKSortCodeValidator",
    "ULIDValidator",
    "UPIIdValidator",
    "URLValidator",
    "USZipCodeValidator",
    "UdyamValidator",
    "VINValidator",
    "VoterIdValidator",
]
