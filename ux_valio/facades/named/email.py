# SPDX-License-Identifier: MIT
"""Email. Addr-spec identity (fullmatch). Not a primitive type."""

from __future__ import annotations

from typing import Any

from ux_valio.facades.typed import StringValidator
from ux_valio.pattern import Pattern, PatternType
from ux_valio.validators.leaves import PatternValidator

# Practical RFC 5322-ish addr-spec. Engine KEEP: PatternValidator findall
# still exists; this facade's extra is fullmatch of the whole string.
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
