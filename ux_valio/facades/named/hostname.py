# SPDX-License-Identifier: MIT
"""DNS hostname / FQDN. RFC 1123 labels. No DNS lookup."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

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
