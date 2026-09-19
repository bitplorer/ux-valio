# SPDX-License-Identifier: MIT
"""India postal / address identity (PIN, state).

Sibling of the other ``india`` layers — does not import them.
Depends on typed. Public names re-export from ``ux_valio`` /
``ux_valio.facades.named.india``.
"""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_PIN = re.compile(r"[1-9][0-9]{5}")

# Administrative 2-letter (Udyam / RTO). Not ISO 3166-2:IN (that uses CT
# for Chhattisgarh; Indian forms use CG).
_IN_STATES = frozenset(
    """
    AN AP AR AS BR CG CH DD DH DL GA GJ HP HR JH JK KA KL LA LD
    MH ML MN MP MZ NL OD PB PY RJ SK TN TR TS UK UP WB
    """.split()
)


class PinCodeValidator(StringValidator):
    """India Post PIN: 6 digits, first 1–9.

    Usage::

        pin: str = PinCodeValidator()

    Non-digits strip; stores compact ``226001``. No locality lookup.
    """

    @staticmethod
    def _is_valid_pincode(value: Any) -> bool:
        return isinstance(value, str) and _PIN.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = "".join(ch for ch in value if ch.isdigit())
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_pincode(value):
            raise ValueError(f"{self.name} is not a valid Indian PIN code")


class IndiaStateCodeValidator(StringValidator):
    """Indian administrative 2-letter state / UT (``MH``, ``DL``, ``CG``).

    Usage::

        state: str = IndiaStateCodeValidator()

    ``mh`` → ``MH``. Udyam/RTO codes, not ISO 3166-2:IN (``CT`` for
    Chhattisgarh is rejected). No gazette lookup.
    """

    @staticmethod
    def _is_valid_state(value: Any) -> bool:
        return isinstance(value, str) and value in _IN_STATES

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().upper()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_state(value):
            raise ValueError(f"{self.name} is not a valid Indian state code")
