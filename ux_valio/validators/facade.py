# SPDX-License-Identifier: MIT
"""Door A facade: dataclass field default that runs concern leaves on a path.

Concern leaves own the validate methods. ``Validator`` does not inherit those
leaves; it binds the same method implementations onto one ordered path.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from ux_valio.validators.async_bridge import invoke_callable
from ux_valio.validators.base import ValidateProperty
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


def _namespace(func: Callable[..., Any], namespace: str | None) -> str:
    """Bag key. valio@3415c03 ``add_pre_validator`` L1861:
    ``namespace or str(func.__qualname__).split(".")[0]``.

    A module-level function without ``namespace=`` keys by the function name,
    which will not match ``instance.__class__.__name__``. A method on a
    nested class (``test_fn.<locals>.Host.fn``) keys by ``test_fn``. Pass
    ``namespace=`` or decorate a method on a module-level host class.
    """
    return namespace or str(func.__qualname__).split(".")[0]


class Validator(ValidateProperty):
    """Door A facade: dataclass field default that composes concern leaves."""

    validation_path = ValidationPath(DEFAULT_PATH_NAMES)

    def __init__(
        self,
        default: Any = None,
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
        logger: Any = False,
        cache_task: bool = True,
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
        self.cache_task = cache_task
        self._custom_validators: dict[str, list[Callable[..., Any]]] = defaultdict(list)
        self._processors: dict[str, dict[str, list[Callable[..., Any]]]] = {
            phase: defaultdict(list)
            for phase in (
                # No "pre_set": ValidateProperty.pre_set *is* pre_validate →
                # validate → post_validate. add_pre_set would be a second door.
                "pre_validate",
                "post_validate",
                "post_set",
                "pre_get",
                "post_get",
                "pre_delete",
                "post_delete",
            )
        }
        self._tasks: dict[str, dict[str, list[Callable[..., Any]]]] = {
            phase: defaultdict(list)
            for phase in self._processors
        }
        super().__init__(
            default=default,
            name=name,
            doc=doc,
            debug=debug,
            logger=logger,
        )

    def notify_pre_set(self, obj: Any) -> None:
        self._assignment_counts.setdefault(id(obj), 0)

    def notify_post_set(self, obj: Any) -> None:
        self._assignment_counts[id(obj)] = self._assignment_counts.get(id(obj), 0) + 1
        self.number_of_assignment += 1

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

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self.validation_path.run(self, instance, value, self._unit_lookup())
        if instance is None:
            return
        for func in self._custom_validators[instance.__class__.__name__]:
            invoke_callable(func, instance, value)

    def add_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._custom_validators[_namespace(func, namespace)].append(func)
        return func

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        for func in self._processors[phase][instance.__class__.__name__]:
            value = invoke_callable(func, instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        for func in self._tasks[phase][instance.__class__.__name__]:
            invoke_callable(func, instance, value)
        return value

    def _process_then_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        value = self._run_processors(phase, instance, value)
        self._run_tasks(phase, instance, value)
        return value

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("pre_validate", instance, value)

    def post_validation_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_validate", instance, value)

    def post_set_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_set", instance, value)

    def pre_get_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("pre_get", instance, value)

    def post_get_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_get", instance, value)

    def pre_delete_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("pre_delete", instance, value)

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_delete", instance, value)

    def add_pre_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["pre_validate"][_namespace(func, namespace)].append(func)
        return func

    def add_post_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["post_validate"][_namespace(func, namespace)].append(func)
        return func

    def add_post_set(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["post_set"][_namespace(func, namespace)].append(func)
        return func

    def add_pre_get(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["pre_get"][_namespace(func, namespace)].append(func)
        return func

    def add_post_get(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["post_get"][_namespace(func, namespace)].append(func)
        return func

    def add_pre_delete(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["pre_delete"][_namespace(func, namespace)].append(func)
        return func

    def add_post_delete(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._processors["post_delete"][_namespace(func, namespace)].append(func)
        return func

    def add_pre_validator_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["pre_validate"][_namespace(func, namespace)].append(func)
        return func

    def add_post_validator_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["post_validate"][_namespace(func, namespace)].append(func)
        return func

    def add_post_set_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["post_set"][_namespace(func, namespace)].append(func)
        return func

    def add_pre_get_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["pre_get"][_namespace(func, namespace)].append(func)
        return func

    def add_post_get_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["post_get"][_namespace(func, namespace)].append(func)
        return func

    def add_pre_delete_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["pre_delete"][_namespace(func, namespace)].append(func)
        return func

    def add_post_delete_task(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._tasks["post_delete"][_namespace(func, namespace)].append(func)
        return func


class IntegerValidator(Validator):
    annotation = int


class StringValidator(Validator):
    annotation = str


class BooleanValidator(Validator):
    annotation = bool
