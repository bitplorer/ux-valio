# SPDX-License-Identifier: MIT
"""URL. scheme + netloc identity. Not a primitive type."""

from __future__ import annotations

import urllib.parse
from typing import Any

from ux_valio.facades.typed import StringValidator


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
