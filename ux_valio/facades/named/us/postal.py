# SPDX-License-Identifier: MIT
"""US postal / address identity (ZIP, state).

Sibling of the other ``us`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.us``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_US_ZIP = re.compile(r"[0-9]{5}(?:[0-9]{4})?")

class USZipCodeValidator(StringValidator):
    """US ZIP: 5 digits or ZIP+4.

    Usage::

        zip: str = USZipCodeValidator()

    ``90210-1234`` → ``902101234``. No USPS lookup.
    """

    @staticmethod
    def _is_valid_zip(value: Any) -> bool:
        return isinstance(value, str) and _US_ZIP.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(char for char in value if char.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_zip(value):
            raise ValueError(f"{self.name} is not a valid US ZIP code")


# USPS 50 + DC + inhabited territories used on shipping forms.
_US_STATES = frozenset(
    """
    AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD
    MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC
    SD TN TX UT VT VA WA WV WI WY DC AS GU MP PR VI
    """.split()
)


class USStateValidator(StringValidator):
    """USPS state / territory 2-letter (``CA``, ``NY``, ``PR``).

    Usage::

        state: str = USStateValidator()

    ``ca`` → ``CA``. Fifty states, DC, AS, GU, MP, PR, VI. No USPS
    lookup.
    """

    @staticmethod
    def _is_valid_state(value: Any) -> bool:
        return isinstance(value, str) and value in _US_STATES

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_state(value):
            raise ValueError(f"{self.name} is not a valid US state code")

