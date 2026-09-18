# SPDX-License-Identifier: MIT
"""Length concern leaves. Min/max/exact are leaf-owned methods."""

from __future__ import annotations

from typing import Any

from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.bounds import bound_value, reject_inverted, specified


class MinLengthValidator(ValidateProperty):
    def __init__(self, min_length: int | None = None, **kwargs: Any) -> None:
        self.min_length = min_length
        super().__init__(**kwargs)

    def _validate_min_length(self: Any, instance: Any, value: Any) -> None:
        min_length = bound_value(self, "min_length")
        if min_length is None or value is None:
            return
        value_length = LengthValidator._len_or_reject(self, value)
        if value_length < min_length:
            raise ValueError(
                f"{self.name} expect the value of minimum length {min_length}, "
                f"got length {value_length} value instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_min_length(instance, value)


class MaxLengthValidator(ValidateProperty):
    def __init__(self, max_length: int | None = None, **kwargs: Any) -> None:
        self.max_length = max_length
        super().__init__(**kwargs)

    def _validate_max_length(self: Any, instance: Any, value: Any) -> None:
        max_length = bound_value(self, "max_length")
        if max_length is None or value is None:
            return
        value_length = LengthValidator._len_or_reject(self, value)
        if value_length > max_length:
            raise ValueError(
                f"{self.name} expect the value of maximum length {max_length}, "
                f"got length {value_length} value instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_max_length(instance, value)


class LengthValidator(ValidateProperty):
    """Exact length plus inclusive min/max. Composes bound checks as methods."""

    def __init__(
        self,
        min_length: int | None = None,
        length: int | None = None,
        max_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        self.bind_bounds(self, min_length, length, max_length)
        super().__init__(**kwargs)

    @staticmethod
    def _len_or_reject(owner: Any, value: Any) -> int:
        """``len(value)``, or a named TypeError when the value is not sized."""
        try:
            return len(value)
        except TypeError:
            raise TypeError(
                f"{owner.name} expect a sized value, got {type(value).__name__} type instead"
            ) from None

    @staticmethod
    def bind_bounds(
        obj: Any, min_length: Any, length: Any, max_length: Any
    ) -> None:
        reject_inverted(min_length, max_length, "max_length can not be less than min_length")
        if specified(min_length, length) and length < min_length:
            raise ValueError("length can not be less than min_length")
        if specified(max_length, length) and max_length < length:
            raise ValueError("length can not be more than max_length")
        obj.min_length = min_length
        obj.max_length = max_length
        obj.length = length

    def _validate_min_length(self, instance: Any, value: Any) -> None:
        MinLengthValidator._validate_min_length(self, instance, value)

    def _validate_max_length(self, instance: Any, value: Any) -> None:
        MaxLengthValidator._validate_max_length(self, instance, value)

    def _validate_exact_length(self, instance: Any, value: Any) -> None:
        length = bound_value(self, "length")
        if length is None or value is None:
            return
        value_length = LengthValidator._len_or_reject(self, value)
        if value_length != length:
            raise ValueError(
                f"{self.name} expect the value of length {length}, "
                f"got length {value_length} value instead"
            )

    def _validate_length(self, instance: Any, value: Any) -> None:
        MinLengthValidator._validate_min_length(self, instance, value)
        MaxLengthValidator._validate_max_length(self, instance, value)
        LengthValidator._validate_exact_length(self, instance, value)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_length(instance, value)
