# SPDX-License-Identifier: MIT
"""Named identity facades. Parallel products on top of ``typed``.

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
other, and ``typed`` never imports this package.
"""

from ux_valio.facades.named.aadhaar import AadhaarCardValidator
from ux_valio.facades.named.bic import BICValidator
from ux_valio.facades.named.cin import CINValidator
from ux_valio.facades.named.ean import EANValidator
from ux_valio.facades.named.email import EmailValidator
from ux_valio.facades.named.expiry import ExpiryValidator
from ux_valio.facades.named.gstin import GSTINValidator
from ux_valio.facades.named.iban import IBANValidator
from ux_valio.facades.named.ifsc import IFSCValidator
from ux_valio.facades.named.imei import IMEIValidator
from ux_valio.facades.named.isbn import ISBNValidator
from ux_valio.facades.named.isin import ISINValidator
from ux_valio.facades.named.mac import MACAddressValidator
from ux_valio.facades.named.pan import PANCardValidator
from ux_valio.facades.named.payment import PaymentCardValidator
from ux_valio.facades.named.phone import PhoneNumberValidator
from ux_valio.facades.named.pincode import PinCodeValidator
from ux_valio.facades.named.tan import TANValidator
from ux_valio.facades.named.upi import UPIIdValidator
from ux_valio.facades.named.url import URLValidator
from ux_valio.facades.named.vin import VINValidator
from ux_valio.facades.named.voter import VoterIdValidator
from ux_valio.facades.named.aba import ABARoutingValidator
from ux_valio.facades.named.card_expiry import CardExpiryValidator
from ux_valio.facades.named.country import CountryCodeValidator
from ux_valio.facades.named.currency import CurrencyCodeValidator
from ux_valio.facades.named.gtin import GTINValidator
from ux_valio.facades.named.hostname import HostnameValidator
from ux_valio.facades.named.hsn import HSNCodeValidator
from ux_valio.facades.named.lei import LEIValidator
from ux_valio.facades.named.slug import SlugValidator
from ux_valio.facades.named.timezone import TimezoneValidator
from ux_valio.facades.named.ulid import ULIDValidator

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
    "URLValidator",
    "VINValidator",
    "VoterIdValidator",
]
