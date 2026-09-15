# SPDX-License-Identifier: MIT
"""Typed Door A facades. No Field/Schema twin; no RGB/HSL; no payment/expiry leaves."""

from __future__ import annotations

import datetime
import decimal
import enum
import ipaddress
import pathlib
import uuid
from typing import Any

from ux_valio.pattern import Pattern
from ux_valio.validators.facade import StringValidator, Validator

# Practical RFC 5322-ish addr-spec. findall substring match (product KEEP).
_EMAIL_PATTERN = Pattern(
    r"(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
    r'"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|'
    r'\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")'
    r"@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?|"
    r"\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-zA-Z0-9-]*[a-zA-Z0-9]:"
    r"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|"
    r'\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])',
    alias="local@example.com",
)


class FloatValidator(Validator):
    annotation = float


class DecimalValidator(Validator):
    annotation = decimal.Decimal


class BytesValidator(Validator):
    annotation = bytes


class DateValidator(Validator):
    """Typed ``datetime.date`` facade. Strings are not parsed."""

    annotation = datetime.date


class EmailValidator(StringValidator):
    def __init__(self, pattern: Any = _EMAIL_PATTERN, **kwargs: Any) -> None:
        super().__init__(pattern=pattern, **kwargs)


class UUIDValidator(Validator):
    annotation = uuid.UUID

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except ValueError as err:
                raise ValueError(f"{self.name} expects a UUID, got {value!r}") from err
        return super().pre_validation_processing(instance, value)


class PathValidator(Validator):
    annotation = pathlib.Path

    def __init__(self, path_exists: bool | None = None, **kwargs: Any) -> None:
        if path_exists is not None and not isinstance(path_exists, bool):
            raise TypeError(
                f"path_exists expected type bool value, got {type(path_exists).__name__} type instead"
            )
        self.path_exists = path_exists
        super().__init__(**kwargs)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = pathlib.Path(value)
        return super().pre_validation_processing(instance, value)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        path = value if isinstance(value, pathlib.Path) else pathlib.Path(value)
        if self.path_exists is True and not path.exists():
            raise FileNotFoundError(f"{self.name} expects an existing path, got {path}")


class IPv4Validator(StringValidator):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        try:
            ipaddress.IPv4Address(value)
        except (ValueError, ipaddress.AddressValueError) as err:
            raise ValueError(
                f"{self.name} expects a valid IPv4 address, got {value} as value instead"
            ) from err


class IPv6Validator(StringValidator):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        try:
            ipaddress.IPv6Address(value)
        except (ValueError, ipaddress.AddressValueError) as err:
            raise ValueError(
                f"{self.name} expects a valid IPv6 address, got {value} as value instead"
            ) from err


class IPAddressValidator(StringValidator):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        try:
            ipaddress.ip_address(value)
        except (ValueError, ipaddress.AddressValueError) as err:
            raise ValueError(
                f"{self.name} expects a valid IP address, got {value} as value instead"
            ) from err


class EnumValidator(Validator):
    """Member of ``enum.Enum``. Class annotation is unset so a concrete enum may own the field."""

    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        if not isinstance(value, enum.Enum):
            raise TypeError(
                f"{self.name} expect {enum.Enum} type, got {type(value).__name__} type instead"
            )


class IntegerEnumValidator(Validator):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        if not isinstance(value, enum.IntEnum):
            raise TypeError(
                f"{self.name} expect {enum.IntEnum} type, got {type(value).__name__} type instead"
            )


class StringEnumValidator(Validator):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        super().validate(instance=instance, value=value)
        if value is None:
            return
        if not isinstance(value, enum.Enum) or not isinstance(value.value, str):
            raise TypeError(
                f"{self.name} expect a str Enum member, got {type(value).__name__} type instead"
            )
