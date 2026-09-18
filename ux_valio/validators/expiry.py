# SPDX-License-Identifier: MIT
"""Expiry Door A facade. Exclusive expire_* kwargs; expire_before is its own bound."""

from __future__ import annotations

import datetime
from typing import Any

from ux_valio.validators.facade import Validator

_DATE_TYPES = (datetime.datetime, datetime.date, datetime.time)


class ExpiryValidator(Validator):
    """Door A facade: reject assignment when *now* matches the exclusive timeline.

    Not ``Validator[datetime]`` — this gates wall-clock on whatever the field
    stores. ``expire_*`` are constructor bounds, not the assigned value's type.
    """

    expiry: Any
    timeline: str | None

    def __init__(
        self,
        expire_after: Any = None,
        expire_on: Any = None,
        expire_before: Any = None,
        **kwargs: Any,
    ) -> None:
        type(self)._configure_expiry(self, expire_after, expire_on, expire_before)
        super().__init__(**kwargs)

    @staticmethod
    def _parse_expiry_datetime(value: Any) -> datetime.datetime:
        """Stdlib ISO / date / datetime / time. Not valio relib / pyparsing."""
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time.min)
        if isinstance(value, datetime.time):
            return datetime.datetime.combine(datetime.date.today(), value)
        if isinstance(value, str):
            try:
                day = datetime.date.fromisoformat(value)
                return datetime.datetime.combine(day, datetime.time.min)
            except ValueError:
                try:
                    return datetime.datetime.fromisoformat(value)
                except ValueError as err:
                    raise ValueError("expiry must have the pattern 'YYYY-MM-DD'") from err
        raise ValueError("expiry must have the pattern 'YYYY-MM-DD'")

    @staticmethod
    def _configure_expiry(
        obj: Any,
        expire_after: Any = None,
        expire_on: Any = None,
        expire_before: Any = None,
    ) -> None:
        """Bind one exclusive timeline. Each kwarg is pattern-checked on itself."""
        specified = [
            ("after", expire_after),
            ("on", expire_on),
            ("before", expire_before),
        ]
        present = [(name, bound) for name, bound in specified if bound is not None]
        if len(present) > 1:
            raise TypeError(
                "expire_after, expire_on, and expire_before are mutually exclusive"
            )
        if not present:
            obj.expiry = None
            obj.timeline = None
            return
        timeline, bound = present[0]
        if isinstance(bound, str):
            ExpiryValidator._parse_expiry_datetime(bound)
        elif not isinstance(bound, _DATE_TYPES):
            raise ValueError("expiry must have the pattern 'YYYY-MM-DD'")
        obj.expiry = bound
        obj.timeline = timeline

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        self._validate_expiry(instance, value)

    def _validate_expiry(self, instance: Any, value: Any) -> None:
        expiry = getattr(self, "expiry", None)
        if expiry is None or value is None:
            return
        parsed = type(self)._parse_expiry_datetime(expiry)
        now = datetime.datetime.now(tz=parsed.tzinfo)
        timeline = getattr(self, "timeline", None)
        if timeline == "after":
            expired = now > parsed
        elif timeline == "on":
            expired = now.date() != parsed.date()
        elif timeline == "before":
            expired = now < parsed
        else:
            raise ValueError("expiry condition not yet found")
        if expired:
            raise ValueError(f"{self.name} expired {timeline} {self.expiry}")
