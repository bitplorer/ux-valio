# SPDX-License-Identifier: MIT
"""Door A facade: dataclass field default that runs concern leaves on a path.

Concern leaves own the validate methods. ``Validator`` does not inherit those
leaves; it binds the same method implementations onto one ordered path.
Hang ``add_*`` here, or on a compose root after ``&`` / ``AllOf``.
"""

from __future__ import annotations

from typing import Any

from ux_valio.descriptor import _UNSET
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.errors import continue_or_raise, raise_collected
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
from ux_valio.validators.path import DEFAULT_PATH_NAMES, Lookup, ValidationPath
from ux_valio.validators.value import ValueValidator


class Validator(HookHost, ValidateProperty):
    """Door A facade: dataclass field default that composes concern leaves."""

    validation_path = ValidationPath(DEFAULT_PATH_NAMES)

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
        cache_task: bool = True,
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
        self.reassign = reassign
        self.number_of_assignment = 0
        self._assignment_counts: dict[int, int] = {}
        self.multiple_of = multiple_of
        ValueValidator.bind_bounds(self, min_value, gt, value, eq, max_value, lt)
        LengthValidator.bind_bounds(self, min_length, length, max_length)
        self.in_choice = in_choice
        self.not_in_choice = not_in_choice
        self._init_hook_bags(cache_task=cache_task)
        super().__init__(
            default=default,
            default_factory=default_factory,
            name=name,
            doc=doc,
            debug=debug,
            logger=logger,
            collect_all=collect_all,
        )

    def notify_pre_set(self, obj: Any) -> None:
        self._assignment_counts.setdefault(id(obj), 0)

    def notify_post_set(self, obj: Any) -> None:
        self._assignment_counts[id(obj)] = self._assignment_counts.get(id(obj), 0) + 1
        self.number_of_assignment += 1

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        self._assignment_counts.pop(id(instance), None)
        return super().post_delete_processing(instance, value)

    def _unit_lookup(self) -> dict[str, Lookup]:
        return {
            "reassignment": ReassignValidator._validate_reassignment,
            "type": TypeValidator._validate_type,
            "required": RequiredValidator._validate_required,
            "pattern": PatternValidator._validate_pattern,
            "multiple_of": MultipleValidator._validate_multiple_of,
            "length": LengthValidator._validate_length,
            "value": ValueValidator._validate_value,
            "choice": ChoiceValidator._validate_choice,
        }

    def _named_extra(self, instance: Any = None, value: Any = None) -> None:
        """Named-facade extra check after the inherited path. Default is none."""

    def validate(self, instance: Any = None, value: Any = None) -> None:
        errors: list[BaseException] = []
        try:
            self.validation_path.run(
                self, instance, value, self._unit_lookup(), collect_all=self.collect_all
            )
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        try:
            self._run_custom_validators(instance, value)
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        try:
            self._named_extra(instance, value)
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        raise_collected(errors, name=self.name)


class IntegerValidator(Validator):
    annotation = int


class StringValidator(Validator):
    annotation = str


class BooleanValidator(Validator):
    annotation = bool
