# SPDX-License-Identifier: MIT
"""How to reach (email, phone, URL, hostname). Parallel to portal.

Does not import sibling named domain modules. Depends on typed
(or the validate door). Public names still re-export from
``ux_valio`` / ``ux_valio.facades.named``.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Any

from ux_valio.facades.typed import StringValidator
from ux_valio.pattern import Pattern, PatternType
from ux_valio.validators.leaves import PatternValidator

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


class EmailValidator(StringValidator):
    """Addr-spec identity of the **whole** string (fullmatch).

    Usage::

        email: str = EmailValidator()

    ``PatternValidator`` findall still exists for ``pattern=`` on other
    fields; this facade's extra is fullmatch so a substring address is
    rejected. No MX lookup.
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

class PhoneNumberValidator(StringValidator):
    """Valid number for an explicit ``region=``.

    Usage::

        phone: str = PhoneNumberValidator(region="IN")

    ``region`` is required (ISO 3166-1 alpha-2 as ``phonenumbers``
    understands it). Leftover: valio defaulted to ``instance.region`` or
    ``"IN"`` — pass ``region=`` here. ``region`` is not a kwarg on
    ``Validator``. Engine: ``pip install ux-valio[phonenumbers]``. No
    carrier / geocoder network.
    """

    @staticmethod
    def _require_phonenumbers():
        """Load the optional ``phonenumbers`` engine. No carrier / geocoder network."""
        try:
            import phonenumbers
        except ImportError as err:
            raise ImportError(
                "PhoneNumberValidator requires the phonenumbers extra: "
                "pip install ux-valio[phonenumbers]"
            ) from err
        return phonenumbers

    def __init__(self, *, region: str, **kwargs: Any) -> None:
        if not isinstance(region, str):
            raise TypeError(
                f"region expected type str value, got {type(region).__name__} type instead"
            )
        self._phonenumbers = type(self)._require_phonenumbers()
        if region not in self._phonenumbers.SUPPORTED_REGIONS:
            raise ValueError(
                f"region {region!r} is not a supported phonenumbers region"
            )
        self.region = region
        super().__init__(**kwargs)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_phone_number(instance, value)

    def _validate_phone_number(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise ValueError(f"{self.name} is not a valid {self.region} phone number")
        phonenumbers = self._phonenumbers
        try:
            parsed = phonenumbers.parse(value, self.region)
        except phonenumbers.NumberParseException as err:
            raise ValueError(
                f"{self.name} is not a valid {self.region} phone number"
            ) from err
        if not phonenumbers.is_valid_number_for_region(parsed, self.region):
            raise ValueError(f"{self.name} is not a valid {self.region} phone number")

class URLValidator(StringValidator):
    """URL identity: scheme + netloc (stdlib ``urlparse``).

    Usage::

        site: str = URLValidator()

    ``https://example.com/path`` is accepted; ``example.com`` (no scheme)
    is rejected. Stores the given string (not rewritten). No DNS lookup.
    """

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not isinstance(value, str):
            raise ValueError(f"{self.name} is not a valid URL")
        parsed = urllib.parse.urlparse(value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"{self.name} is not a valid URL")

_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_HOST = re.compile(rf"{_LABEL}(?:\.{_LABEL})*")
_DOTTED_QUAD = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")


class HostnameValidator(StringValidator):
    """DNS hostname identity (no scheme). Complements ``URLValidator``.

    Usage::

        host: str = HostnameValidator()

    ``API.Example.COM.`` → ``api.example.com``. IDN goes to punycode.
    Dotted-quad IPv4 is rejected (use ``IPv4Validator``). No DNS lookup.
    """

    @staticmethod
    def _is_valid_hostname(value: Any) -> bool:
        if not isinstance(value, str) or not (1 <= len(value) <= 253):
            return False
        if _DOTTED_QUAD.fullmatch(value) is not None:
            return False
        return _HOST.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().rstrip(".").lower()
            try:
                value = value.encode("idna").decode("ascii")
            except UnicodeError:
                pass
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_hostname(value):
            raise ValueError(f"{self.name} is not a valid hostname")
