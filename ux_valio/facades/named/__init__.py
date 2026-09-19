# SPDX-License-Identifier: MIT
"""Named identity facades. Parallel products on top of ``typed``.

Each module subclasses ``StringValidator`` (or ``Validator`` for expiry).
They import ``ux_valio.facades.typed`` or the validate door — never each
other, and ``typed`` never imports this package.
"""

from ux_valio.facades.named.aadhaar import AadhaarCardValidator
from ux_valio.facades.named.email import EmailValidator
from ux_valio.facades.named.expiry import ExpiryValidator
from ux_valio.facades.named.gstin import GSTINValidator
from ux_valio.facades.named.iban import IBANValidator
from ux_valio.facades.named.ifsc import IFSCValidator
from ux_valio.facades.named.imei import IMEIValidator
from ux_valio.facades.named.pan import PANCardValidator
from ux_valio.facades.named.payment import PaymentCardValidator
from ux_valio.facades.named.phone import PhoneNumberValidator
from ux_valio.facades.named.pincode import PinCodeValidator
from ux_valio.facades.named.upi import UPIIdValidator
from ux_valio.facades.named.url import URLValidator

__all__ = [
    "AadhaarCardValidator",
    "EmailValidator",
    "ExpiryValidator",
    "GSTINValidator",
    "IBANValidator",
    "IFSCValidator",
    "IMEIValidator",
    "PANCardValidator",
    "PaymentCardValidator",
    "PhoneNumberValidator",
    "PinCodeValidator",
    "UPIIdValidator",
    "URLValidator",
]
