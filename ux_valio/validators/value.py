# SPDX-License-Identifier: MIT
"""Value-bound concern leaves. Min/max/eq are leaf-owned methods."""

from __future__ import annotations

from typing import Any

from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.bounds import bound_value, reject_exclusive, reject_inverted, specified


class MinValueValidator(ValidateProperty):
    def __init__(
        self,
        min_value: Any = None,
        gt: Any = None,
        **kwargs: Any,
    ) -> None:
        reject_exclusive(
            min_value, gt, "min_value and gt both can't be initialized, select one"
        )
        self.min_value = min_value
        self.gt = gt
        super().__init__(**kwargs)

    def _validate_min_value(self, instance: Any, value: Any) -> None:
        if value is None:
            return
        min_value = bound_value(self, "min_value")
        gt = bound_value(self, "gt")
        if min_value is not None and value < min_value:
            raise ValueError(
                f"{self.name} expect the minimum value of {min_value}, got {value} instead"
            )
        if gt is not None and value <= gt:
            raise ValueError(
                f"{self.name} expect a value greater than {gt}, got {value} instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_min_value(instance, value)


class MaxValueValidator(ValidateProperty):
    def __init__(
        self,
        max_value: Any = None,
        lt: Any = None,
        **kwargs: Any,
    ) -> None:
        reject_exclusive(
            max_value, lt, "max_value and lt both can't be initialized, select one"
        )
        self.max_value = max_value
        self.lt = lt
        super().__init__(**kwargs)

    def _validate_max_value(self, instance: Any, value: Any) -> None:
        if value is None:
            return
        max_value = bound_value(self, "max_value")
        lt = bound_value(self, "lt")
        if max_value is not None and value > max_value:
            raise ValueError(
                f"{self.name} expect the maximum value of {max_value}, got {value} instead"
            )
        if lt is not None and value >= lt:
            raise ValueError(
                f"{self.name} expect a value less than {lt}, got {value} instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_max_value(instance, value)


class ValueValidator(ValidateProperty):
    """Inclusive min/max, exclusive gt/lt, exact value/eq. Composes bound checks."""

    def __init__(
        self,
        min_value: Any = None,
        gt: Any = None,
        value: Any = None,
        eq: Any = None,
        max_value: Any = None,
        lt: Any = None,
        **kwargs: Any,
    ) -> None:
        self.bind_bounds(self, min_value, gt, value, eq, max_value, lt)
        super().__init__(**kwargs)

    @staticmethod
    def bind_bounds(
        obj: Any,
        min_value: Any,
        gt: Any,
        value: Any,
        eq: Any,
        max_value: Any,
        lt: Any,
    ) -> None:
        reject_exclusive(
            max_value, lt, "max_value and lt both can't be initialized, select one"
        )
        reject_exclusive(
            min_value, gt, "min_value and gt both can't be initialized, select one"
        )
        reject_exclusive(value, eq, "value and eq both can't be initialized, select one")
        if value is None:
            value = eq
        label = "value" if eq is None else "eq"
        reject_inverted(min_value, max_value, "max_value can not be less than min_value")
        reject_inverted(gt, lt, "lt can not be less than gt")
        if specified(min_value, value) and value < min_value:
            raise ValueError(f"{label} can not be less than min_value")
        if specified(gt, value) and value <= gt:
            raise ValueError(f"{label} can not be less than or equal to gt")
        if specified(max_value, value) and max_value < value:
            raise ValueError(f"{label} can not be more than max_value")
        if specified(lt, value) and value >= lt:
            raise ValueError(f"{label} can not be more than or equal to lt")
        obj.min_value = min_value
        obj.gt = gt
        obj.max_value = max_value
        obj.lt = lt
        obj.value = value

    def _validate_min_value(self, instance: Any, value: Any) -> None:
        MinValueValidator._validate_min_value(self, instance, value)

    def _validate_max_value(self, instance: Any, value: Any) -> None:
        MaxValueValidator._validate_max_value(self, instance, value)

    def _validate_eq_value(self, instance: Any, value: Any) -> None:
        of_value = bound_value(self, "value")
        if of_value is not None and value is not None and value != of_value:
            raise ValueError(
                f"{self.name} expect the value {of_value}, got {value} as value instead"
            )

    def _validate_value(self, instance: Any, value: Any) -> None:
        MinValueValidator._validate_min_value(self, instance, value)
        MaxValueValidator._validate_max_value(self, instance, value)
        ValueValidator._validate_eq_value(self, instance, value)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_value(instance, value)
