# SPDX-License-Identifier: MIT
"""Named identity facades, grouped by where they are used.

Sibling domain modules (parallel, do not import each other)::

    india/    — KYC / GST / registry / bank
    us/       — postal / bank / market / kyc
    uk/       — postal / bank / kyc
    canada/   — postal / kyc
    mexico/   — bank / kyc
    finance/  — international rails / market / card / ISO currency
    catalog   — goods (ISBN, ISSN, EAN, GTIN, VIN)
    contact   — how to reach (Email, Phone, URL, Hostname)
    device    — hardware (IMEI, MAC)
    portal    — SaaS (Slug, Country, Timezone, ULID, Locale, SemVer)
    expiry    — wall-clock ``ExpiryValidator`` (not a string identity)

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

from ux_valio.facades.named.canada import (
    CAPostalCodeValidator,
    CanadianSINValidator,
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
from ux_valio.facades.named.mexico import CLABEValidator, MexicoRFCValidator
from ux_valio.facades.named.uk import (
    NINOValidator,
    UKPostcodeValidator,
    UKSortCodeValidator,
)
from ux_valio.facades.named.us import (
    ABARoutingValidator,
    CUSIPValidator,
    EINValidator,
    SSNValidator,
    USZipCodeValidator,
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
    "AadhaarCardValidator",
    "ABARoutingValidator",
    "BICValidator",
    "CanadianSINValidator",
    "CAPostalCodeValidator",
    "CardExpiryValidator",
    "CINValidator",
    "CLABEValidator",
    "CountryCodeValidator",
    "CurrencyCodeValidator",
    "CUSIPValidator",
    "DINValidator",
    "EANValidator",
    "EINValidator",
    "EmailValidator",
    "ExpiryValidator",
    "FSSAIValidator",
    "GSTINValidator",
    "GTINValidator",
    "HostnameValidator",
    "HSNCodeValidator",
    "IBANValidator",
    "IFSCValidator",
    "IMEIValidator",
    "IndianPassportValidator",
    "ISBNValidator",
    "ISINValidator",
    "ISSNValidator",
    "LEIValidator",
    "LLPINValidator",
    "LocaleValidator",
    "MACAddressValidator",
    "MexicoRFCValidator",
    "NINOValidator",
    "PANCardValidator",
    "PaymentCardValidator",
    "PhoneNumberValidator",
    "PinCodeValidator",
    "SemVerValidator",
    "SlugValidator",
    "SSNValidator",
    "TANValidator",
    "TimezoneValidator",
    "UdyamValidator",
    "UKPostcodeValidator",
    "UKSortCodeValidator",
    "ULIDValidator",
    "UPIIdValidator",
    "URLValidator",
    "USZipCodeValidator",
    "VINValidator",
    "VoterIdValidator",
]
