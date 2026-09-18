# SPDX-License-Identifier: MIT
"""Door A validators, layered.

Who depends on whom (top is core, bottom inherits):

- ``ux_valio.descriptor`` — ``Property`` (store door). Depends on
  ``ux_valio.errors`` only, never on this package.
- ``ux_valio.errors`` — ``ValidationErrors`` (shared collect-all type).
- ``ux_valio.pattern`` — pattern algebra. Independent of the descriptor.
- this package — validate door (``ValidateProperty`` : ``Property``):
  - ``base`` — ``ValidateProperty``
  - ``hooks`` — ``HookHost`` mixin (parallel to ``ValidateProperty``)
  - ``leaves`` / ``length`` / ``value`` — concern leaves : ``ValidateProperty``
    (parallel to each other; object-compose with ``&`` / ``|``, no leaf MI)
  - ``compose`` — ``AllOf`` / ``AnyOf`` : ``HookHost`` + ``ValidateProperty``
  - ``facade`` — ``Validator`` : ``HookHost`` + ``ValidateProperty``
    (unit list ``ValidationPath`` lives here, not ``PathValidator``)
  - named facades (``typed``, ``payment``, ``expiry``, ``phone``,
    ``aadhaar``, ``pan``) : ``Validator`` (parallel to each other)

Length/value checks are leaf-owned methods. ``check_*`` free functions are not
the public API. ``AttributeValidator`` is not shipped — object-attribute
presence checks belong at the call site or on ``add_validator``.
"""

from ux_valio.errors import ValidationErrors
from ux_valio.validators.aadhaar import AadhaarCardValidator
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.compose import AllOf, AnyOf, Chain
from ux_valio.validators.expiry import ExpiryValidator
from ux_valio.validators.facade import Validator
from ux_valio.validators.leaves import (
    ChoiceValidator,
    MultipleValidator,
    PatternValidator,
    ReassignValidator,
    RequiredValidator,
    TypeValidator,
)
from ux_valio.validators.length import LengthValidator, MaxLengthValidator, MinLengthValidator
from ux_valio.validators.pan import PANCardValidator
from ux_valio.validators.payment import PaymentCardValidator
from ux_valio.validators.phone import PhoneNumberValidator
from ux_valio.validators.typed import (
    BooleanValidator,
    BytesValidator,
    DateTimeValidator,
    DateValidator,
    DecimalValidator,
    EmailValidator,
    EnumValidator,
    FloatValidator,
    IntegerEnumValidator,
    IntegerValidator,
    IPAddressValidator,
    IPv4Validator,
    IPv6Validator,
    PathValidator,
    StringEnumValidator,
    StringValidator,
    URLValidator,
    UUIDValidator,
)
from ux_valio.validators.value import MaxValueValidator, MinValueValidator, ValueValidator

__all__ = [
    "AadhaarCardValidator",
    "AllOf",
    "AnyOf",
    "BooleanValidator",
    "BytesValidator",
    "Chain",
    "ChoiceValidator",
    "DateTimeValidator",
    "DateValidator",
    "DecimalValidator",
    "EmailValidator",
    "EnumValidator",
    "ExpiryValidator",
    "FloatValidator",
    "IPAddressValidator",
    "IPv4Validator",
    "IPv6Validator",
    "IntegerEnumValidator",
    "IntegerValidator",
    "LengthValidator",
    "MaxLengthValidator",
    "MaxValueValidator",
    "MinLengthValidator",
    "MinValueValidator",
    "MultipleValidator",
    "PANCardValidator",
    "PathValidator",
    "PaymentCardValidator",
    "PhoneNumberValidator",
    "PatternValidator",
    "ReassignValidator",
    "RequiredValidator",
    "StringEnumValidator",
    "StringValidator",
    "TypeValidator",
    "UUIDValidator",
    "URLValidator",
    "ValidateProperty",
    "ValidationErrors",
    "Validator",
    "ValueValidator",
]
