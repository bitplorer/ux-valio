# SPDX-License-Identifier: MIT
"""Descriptor field default that runs concern leaves in a fixed order.

Concern leaves own the validate methods. ``Validator`` does not inherit those
leaves; it calls the same implementations, in order, on one path.
Hang ``add_*`` here, or on a compose root after ``&`` / ``AllOf``.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, TypeVar

from ux_valio.descriptor import _UNSET
from ux_valio.errors import continue_or_raise, raise_collected, run_steps
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.hooks import HookHost
from ux_valio.validators.leaves import (
    ChoiceValidator,
    MultipleValidator,
    PatternValidator,
    ReassignValidator,
    RequiredValidator,
    TypeValidator,
)
from ux_valio.validators.length import LengthValidator
from ux_valio.validators.value import ValueValidator

T = TypeVar("T")
Lookup = Callable[[Any, Any, Any], Any]


class ValidationPath:
    """Ordered unique concern callables. A second ``validate()`` is a new pass."""

    def __init__(self, units: Iterable[Lookup]) -> None:
        units = tuple(units)
        seen: set[Lookup] = set()
        for unit in units:
            if unit in seen:
                raise ValueError(f"validation path double-call: {unit!r}")
            seen.add(unit)
        self.units = units

    def run(
        self,
        owner: Any,
        instance: Any,
        value: Any,
        collect_all: bool = False,
    ) -> list[Any]:
        ran: set[Lookup] = set()
        results: list[Any] = []
        errors: list[BaseException] = []
        for unit in self.units:
            if unit in ran:
                raise ValueError(f"validation path double-call: {unit!r}")
            ran.add(unit)
            try:
                results.append(unit(owner, instance, value))
            except Exception as err:
                continue_or_raise(collect_all, errors, err)
                results.append(None)
        raise_collected(errors, name=getattr(owner, "name", None))
        return results


DEFAULT_PATH_UNITS = (
    ReassignValidator._validate_reassignment,
    TypeValidator._validate_type,
    RequiredValidator._validate_required,
    PatternValidator._validate_pattern,
    MultipleValidator._validate_multiple_of,
    LengthValidator._validate_length,
    ValueValidator._validate_value,
    ChoiceValidator._validate_choice,
)


class Validator(HookHost, ValidateProperty[T]):
    """Descriptor field default that composes concern leaves.

    ``Validator[int]`` declares the stored type (one argument). Named
    facades specialize it (``IntegerValidator`` is ``Validator[int]``).
    """

    validation_path = ValidationPath(DEFAULT_PATH_UNITS)

    def __init__(
        self,
        default: Any = None,
        default_factory: Any = None,
        name: str | None = None,
        doc: str | None = None,
        required: bool | None = None,
        pattern: Any = None,
        reassign: bool | None = None,
        multiple_of: Any = None,
        min_value: Any = None,
        value: Any = None,
        max_value: Any = None,
        gt: Any = None,
        eq: Any = None,
        lt: Any = None,
        min_length: int | None = None,
        length: int | None = None,
        max_length: int | None = None,
        in_choice: Any = None,
        not_in_choice: Any = None,
        debug: bool | None = None,
        logger: Any = _UNSET,
        collect_all: Any = _UNSET,
    ) -> None:
        if required is not None and not isinstance(required, bool):
            raise TypeError(
                f"required expected type bool value, got {type(required).__name__} type instead"
            )
        if reassign is not None and not isinstance(reassign, bool):
            raise TypeError(
                f"reassign expected type bool value, got {type(reassign).__name__} type instead"
            )
        self.required = required
        self.pattern = pattern
        self._compiled = None
        self._compiled_source = object()
        self.reassign = reassign
        self.number_of_assignment = 0
        self._assignment_counts: dict[int, int] = {}
        self._assignment_alive: dict[int, Any] = {}
        self.multiple_of = multiple_of
        ValueValidator.bind_bounds(self, min_value, gt, value, eq, max_value, lt)
        LengthValidator.bind_bounds(self, min_length, length, max_length)
        self.in_choice = in_choice
        self.not_in_choice = not_in_choice
        ChoiceValidator._reject_non_container("in_choice", in_choice)
        ChoiceValidator._reject_non_container("not_in_choice", not_in_choice)
        super().__init__(
            default=default,
            default_factory=default_factory,
            name=name,
            doc=doc,
            debug=debug,
            logger=logger,
            collect_all=collect_all,
        )

    _watch_assignment = ReassignValidator._watch_assignment

    def notify_pre_set(self, obj: Any) -> None:
        ReassignValidator.notify_pre_set(self, obj)

    def notify_post_set(self, obj: Any) -> None:
        ReassignValidator.notify_post_set(self, obj)

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        ReassignValidator.post_delete_processing(self, instance, value)
        return super().post_delete_processing(instance, value)

    def _validate_named_facade(self, instance: Any = None, value: Any = None) -> None:
        """Named-facade extra check after the inherited path. Default is none."""

    def validate(self, instance: Any = None, value: Any = None) -> None:
        run_steps(
            (
                lambda: self.validation_path.run(
                    self, instance, value, collect_all=self.collect_all
                ),
                lambda: self._run_custom_validators(instance, value),
                lambda: self._validate_named_facade(instance, value),
            ),
            self.collect_all,
            self.name,
        )
