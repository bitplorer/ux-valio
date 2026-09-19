# SPDX-License-Identifier: MIT
"""Typed Door A facades. No Field/Schema twin; no RGB/HSL; no HexColor public facade.

Construction is ``Any`` to type checkers (``ValidateProperty.__new__``), so
``name: str = StringValidator()`` and a custom ``owner: User = UserValidator()``
both assign. Runtime the object is still this descriptor. Set ``annotation``
to the stored type — that is the type door, not a per-type mixin.
"""

from __future__ import annotations

import datetime
import decimal
import enum
import ipaddress
import pathlib
import re
import urllib.parse
import uuid
from typing import Any

from ux_valio.pattern import Pattern, PatternType
from ux_valio.validators.facade import Validator
from ux_valio.validators.leaves import PatternValidator

# Practical RFC 5322-ish addr-spec. EmailValidator fullmatch extra; engine KEEP.
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


class IntegerValidator(Validator[int]):
    annotation = int


class StringValidator(Validator[str]):
    annotation = str


class BooleanValidator(Validator[bool]):
    annotation = bool


class FloatValidator(Validator[float]):
    annotation = float


class DecimalValidator(Validator[decimal.Decimal]):
    annotation = decimal.Decimal | str

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return super().pre_validation_processing(
            instance, self._coerce_str(value, decimal.Decimal, "Decimal")
        )

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, decimal.Decimal)


class BytesValidator(Validator[bytes]):
    annotation = bytes


_EU_DATE = re.compile(r"(\d{4})([-:/])(\d{1,2})\2(\d{1,2})")
_IND_DATE = re.compile(r"(\d{1,2})([-:/])(\d{1,2})\2(\d{4})")


class DateValidator(Validator[datetime.date]):
    annotation = datetime.date | str

    @staticmethod
    def _parse_eu_ind_date(text: str) -> datetime.date | None:
        eu = _EU_DATE.fullmatch(text)
        if eu is not None:
            year, _, month, day = eu.groups()
            try:
                return datetime.date(int(year), int(month), int(day))
            except ValueError:
                return None
        ind = _IND_DATE.fullmatch(text)
        if ind is not None:
            day, _, month, year = ind.groups()
            try:
                return datetime.date(int(year), int(month), int(day))
            except ValueError:
                return None
        return None

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            parsed = type(self)._parse_eu_ind_date(value)
            if parsed is None:
                raise ValueError(
                    f"{self.name} expects a calendar date in EU YYYY-MM-DD "
                    f"or IND DD-MM-YYYY (delimiters -, /, :), got {value!r}"
                )
            value = parsed
        return super().pre_validation_processing(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if isinstance(value, datetime.datetime):
            raise TypeError(
                f"{self.name} expect {datetime.date} type, got {type(value).__name__} type instead"
            )
        self._reject_unless_instance(value, datetime.date)


class DateTimeValidator(Validator[datetime.datetime]):
    """Door A datetime facade. Stores ``datetime.datetime``. ISO via fromisoformat.

    Plain ``datetime.date`` is rejected (that is ``DateValidator``). Date-only
    ISO strings follow stdlib ``datetime.fromisoformat`` (midnight on 3.11+).
    Owner annotation may be ``datetime.datetime``, ``str``, or the union.
    """

    annotation = datetime.datetime | str

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return super().pre_validation_processing(
            instance, self._coerce_str(value, datetime.datetime.fromisoformat, "ISO datetime")
        )

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, datetime.datetime)


class EmailValidator(StringValidator):
    """Door A email facade. Identity of the whole string, not findall substring.

    PatternValidator still matches with findall. This facade adds a fullmatch
    extra so the name EmailValidator is true.
    """

    def __init__(self, pattern: Any = _EMAIL_PATTERN, **kwargs: Any) -> None:
        super().__init__(pattern=pattern, **kwargs)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise ValueError(f"{self.name} is not a valid email address")
        pattern = self.pattern
        source = pattern.pattern if isinstance(pattern, PatternType) else pattern
        if not isinstance(source, str):
            raise ValueError(f"{self.name} is not a valid email address")
        compiled = PatternValidator._compiled_finder(self, source)
        if compiled.fullmatch(value) is None:
            raise ValueError(f"{self.name} is not a valid email address")


class URLValidator(StringValidator):
    """Door A URL facade. Identity is scheme + netloc (stdlib ``urlparse``)."""

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise ValueError(f"{self.name} is not a valid URL")
        parsed = urllib.parse.urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"{self.name} is not a valid URL")


class UUIDValidator(Validator[uuid.UUID]):
    annotation = uuid.UUID | str

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return super().pre_validation_processing(
            instance, self._coerce_str(value, uuid.UUID, "UUID")
        )

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, uuid.UUID)


class PathValidator(Validator[pathlib.Path]):
    annotation = pathlib.Path | str

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

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, pathlib.Path)
        if value is not None and self.path_exists is True and not value.exists():
            raise FileNotFoundError(f"{self.name} expects an existing path, got {value}")


def _reject_unless_ip(owner: Any, value: Any, parser: Any, label: str) -> None:
    if value is None:
        return
    try:
        parser(value)
    except (ValueError, ipaddress.AddressValueError) as err:
        raise ValueError(
            f"{owner.name} expects a valid {label}, got {value} as value instead"
        ) from err


class IPv4Validator(StringValidator):
    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        _reject_unless_ip(self, value, ipaddress.IPv4Address, "IPv4 address")


class IPv6Validator(StringValidator):
    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        _reject_unless_ip(self, value, ipaddress.IPv6Address, "IPv6 address")


class IPAddressValidator(StringValidator):
    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        _reject_unless_ip(self, value, ipaddress.ip_address, "IP address")


class EnumValidator(Validator[enum.Enum]):
    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, enum.Enum)


class IntegerEnumValidator(Validator[enum.IntEnum]):
    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, enum.IntEnum)


class StringEnumValidator(Validator[enum.Enum]):
    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, enum.Enum) or not isinstance(value.value, str):
            raise TypeError(
                f"{self.name} expect a str Enum member, got {type(value).__name__} type instead"
            )
