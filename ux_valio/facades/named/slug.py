# SPDX-License-Identifier: MIT
"""URL slug. ``foo-bar`` identity. Does not slugify spaces."""

from __future__ import annotations

import re
from typing import Any

from ux_valio.facades.typed import StringValidator

_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class SlugValidator(StringValidator):
    """Product / tenant / page slug.

    Usage::

        slug: str = SlugValidator()

    Stores lowercase. ``Hello-World`` → ``hello-world``. Spaces and
    underscores are rejected — hang ``pre_validate`` to slugify. No
    uniqueness lookup.
    """

    @staticmethod
    def _is_valid_slug(value: Any) -> bool:
        return isinstance(value, str) and _SLUG.fullmatch(value) is not None

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        if isinstance(value, str):
            value = value.strip().lower()
        return super()._pre_validate(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        if value is None:
            return
        if not type(self)._is_valid_slug(value):
            raise ValueError(f"{self.name} is not a valid slug")
