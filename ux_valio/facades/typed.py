# SPDX-License-Identifier: MIT
"""Typed validator facades. No Field/Schema twin; no RGB/HSL; no HexColor public facade.

Primitives and stdlib store types live here. String identities (email, URL,
GSTIN, …) live in ``facades.named``. Construction is ``Any`` to type checkers
(``ValidateProperty.__new__``), so ``name: str = StringValidator()`` assigns.
"""

from __future__ import annotations

import datetime
import decimal
import enum
import ipaddress
import pathlib
import re
import uuid
from typing import Any

from ux_valio.validators.facade import Validator


class IntegerValidator(Validator[int]):
    """Stored ``int``.

    Usage::

        n: int = IntegerValidator(min_value=0)
    """

    annotation = int


class StringValidator(Validator[str]):
    """Stored ``str``.

    Usage::

        name: str = StringValidator(max_length=50)
    """

    annotation = str


class BooleanValidator(Validator[bool]):
    """Stored ``bool``.

    Usage::

        active: bool = BooleanValidator()
    """

    annotation = bool


class FloatValidator(Validator[float]):
    """Stored ``float``.

    Usage::

        ratio: float = FloatValidator(min_value=0.0)
    """

    annotation = float


class DecimalValidator(Validator[decimal.Decimal]):
    """Stores ``decimal.Decimal``. Coerces Decimal strings; rejects float.

    Usage::

        amount: Decimal = DecimalValidator(min_value=Decimal("0.01"))
    """

    annotation = decimal.Decimal | str

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        return super()._pre_validate(
            instance, self._coerce_str(value, decimal.Decimal, "Decimal")
        )

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, decimal.Decimal)


class BytesValidator(Validator[bytes]):
    """Stored ``bytes``.

    Usage::

        blob: bytes = BytesValidator()
    """

    annotation = bytes


_EU_DATE = re.compile(r"(\d{4})([-:/])(\d{1,2})\2(\d{1,2})")
_IND_DATE = re.compile(r"(\d{1,2})([-:/])(\d{1,2})\2(\d{4})")


class DateValidator(Validator[datetime.date]):
    """Stores ``datetime.date``. EU ``YYYY-MM-DD`` / IND ``DD-MM-YYYY``.

    Usage::

        opened: date = DateValidator()
    """

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

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            parsed = type(self)._parse_eu_ind_date(value)
            if parsed is None:
                raise ValueError(
                    f"{self.name} expects a calendar date in EU YYYY-MM-DD "
                    f"or IND DD-MM-YYYY (delimiters -, /, :), got {value!r}"
                )
            value = parsed
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if isinstance(value, datetime.datetime):
            raise TypeError(
                f"{self.name} expect {datetime.date} type, got {type(value).__name__} type instead"
            )
        self._reject_unless_instance(value, datetime.date)


class DateTimeValidator(Validator[datetime.datetime]):
    """Stores ``datetime.datetime``. ISO via fromisoformat.

    Usage::

        stamped: datetime = DateTimeValidator()

    Plain ``datetime.date`` is rejected (that is ``DateValidator``). Date-only
    ISO strings follow stdlib ``datetime.fromisoformat`` (midnight on 3.11+).
    Owner annotation may be ``datetime.datetime``, ``str``, or the union.
    """

    annotation = datetime.datetime | str

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        return super()._pre_validate(
            instance, self._coerce_str(value, datetime.datetime.fromisoformat, "ISO datetime")
        )

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, datetime.datetime)


class UUIDValidator(Validator[uuid.UUID]):
    """Stores ``uuid.UUID``. Coerces UUID strings.

    Usage::

        public_id: uuid.UUID = UUIDValidator()
    """

    annotation = uuid.UUID | str

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        return super()._pre_validate(
            instance, self._coerce_str(value, uuid.UUID, "UUID")
        )

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, uuid.UUID)


class PathValidator(Validator[pathlib.Path]):
    """Stores ``pathlib.Path``. Coerces ``str``. ``path_exists=True`` is FS.

    Usage::

        folder: Path = PathValidator(path_exists=True)
    """

    annotation = pathlib.Path | str

    def __init__(self, path_exists: bool | None = None, **kwargs: Any) -> None:
        if path_exists is not None and not isinstance(path_exists, bool):
            raise TypeError(
                f"path_exists expected type bool value, got {type(path_exists).__name__} type instead"
            )
        self.path_exists = path_exists
        super().__init__(**kwargs)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = pathlib.Path(value)
        return super()._pre_validate(instance, value)

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
    """Stores the given string if it is an IPv4 address.

    Usage::

        host: str = IPv4Validator()
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        _reject_unless_ip(self, value, ipaddress.IPv4Address, "IPv4 address")


class IPv6Validator(StringValidator):
    """Stores the given string if it is an IPv6 address.

    Usage::

        host: str = IPv6Validator()
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        _reject_unless_ip(self, value, ipaddress.IPv6Address, "IPv6 address")


class IPAddressValidator(StringValidator):
    """Stores the given string if it is IPv4 or IPv6.

    Usage::

        host: str = IPAddressValidator()
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        _reject_unless_ip(self, value, ipaddress.ip_address, "IP address")


class EnumValidator(Validator[enum.Enum]):
    """Stores an ``enum.Enum`` member.

    Usage::

        kind: Color = EnumValidator()
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, enum.Enum)


class IntegerEnumValidator(Validator[enum.IntEnum]):
    """Stores an ``enum.IntEnum`` member.

    Usage::

        level: Level = IntegerEnumValidator()
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._reject_unless_instance(value, enum.IntEnum)


class StringEnumValidator(Validator[enum.Enum]):
    """Stores an ``enum.Enum`` member whose ``.value`` is ``str``.

    Usage::

        rank: Rank = StringEnumValidator()
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, enum.Enum) or not isinstance(value.value, str):
            raise TypeError(
                f"{self.name} expect a str Enum member, got {type(value).__name__} type instead"
            )
