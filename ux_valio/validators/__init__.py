# SPDX-License-Identifier: MIT
"""Door A validators, layered.

``descriptor.Property`` is the store door (package root).
This package is the validate door, in one stack:

- ``base`` — ``ValidateProperty`` (pre_set validates, then store)
- ``hooks`` — ``HookHost`` (``add_*`` bags; compose roots and ``Validator``)
- ``leaves`` — single-concern units + type door (``TypeValidator._ORIGIN_CHECKERS``)
- ``length`` / ``value`` / ``bounds`` — bound concerns
- ``path`` — ordered unique units on the facade
- ``compose`` — ``AllOf`` / ``AnyOf`` (object composition, not leaf MI)
- ``facade`` — ``Validator`` (path of leaves, hang ``add_*`` here)
- named facades (``typed``, ``payment``, ``expiry``, ``phone``, ``aadhaar``, ``pan``)

Length/value checks are leaf-owned methods. ``check_*`` free functions are not
the public API. ``AttributeValidator`` is not shipped — object-attribute
presence checks belong at the call site or on ``add_validator``.
"""

from ux_valio.validators.aadhaar import AadhaarCardValidator
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.compose import AllOf, AnyOf, Chain
from ux_valio.validators.errors import ValidationErrors
from ux_valio.validators.expiry import ExpiryValidator
from ux_valio.validators.facade import BooleanValidator, IntegerValidator, StringValidator, Validator
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
    BytesValidator,
    DateTimeValidator,
    DateValidator,
    DecimalValidator,
    EmailValidator,
    EnumValidator,
    FloatValidator,
    IntegerEnumValidator,
    IPAddressValidator,
    IPv4Validator,
    IPv6Validator,
    PathValidator,
    StringEnumValidator,
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
