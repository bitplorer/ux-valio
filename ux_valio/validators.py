# SPDX-License-Identifier: MIT
"""Concern leaves + ordered validation path (A9 units 2–5).

Compose, do not inherit. ``Validator`` assembles Type / Required / Pattern /
Length / Value-bounds / Multiple / Choice / Reassign on an ordered
``ValidationPath``. Double-call and aggregate+leaf fail closed. A second
``validate()`` is a new pass.

Bound presence is None-only: ``0`` is specified. ``gt``/``lt`` exclusive;
``min_value``/``max_value`` inclusive. Multiple-of is remainder;
``multiple_of=0`` accepts only ``0``.

Processors run then tasks run once. Only the ``pre_set`` processor return
is stored. No asyncio.run in the setter.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Iterable, get_args, get_origin

from ux_valio.descriptor import Property
from ux_valio.pattern import PatternType

Lookup = Callable[["ValidateProperty", Any, Any], Any]


def _is_instance_of(value: Any, annotation: Any) -> bool:
    if annotation is None:
        return True
    origin = get_origin(annotation)
    if origin is None:
        try:
            return isinstance(value, annotation)
        except TypeError:
            return True
    if origin is type(None):
        return value is None
    args = tuple(arg for arg in get_args(annotation) if arg is not type(None))
    if not args:
        return value is None
    try:
        return isinstance(value, args)
    except TypeError:
        return True


def specified(*bounds: Any) -> bool:
    """True when every bound is present. None-only; ``0`` is specified."""
    return all(bound is not None for bound in bounds)


def _reject_exclusive(left: Any, right: Any, message: str) -> None:
    if specified(left, right):
        raise ValueError(message)


def _reject_inverted(lo: Any, hi: Any, message: str) -> None:
    if specified(lo, hi) and hi < lo:
        raise ValueError(message)


def _bound(owner: Any, name: str) -> Any:
    value = getattr(owner, name, None)
    return value if value is not None else None


def _namespace(func: Callable[..., Any], namespace: str | None) -> str:
    return namespace or str(func.__qualname__).split(".")[0]


class ValidateProperty(Property, ABC):
    """Descriptor that validates in ``pre_set`` before store."""

    def pre_set(self, obj: Any, value: Any) -> Any:
        value = self.pre_validation_processing(obj, value)
        self.validate(instance=obj, value=value)
        return self.post_validation_processing(obj, value)

    def post_set(self, obj: Any, value: Any) -> Any:
        return self.post_set_processing(obj, value)

    def pre_get(self, obj: Any, value: Any) -> Any:
        return self.pre_get_processing(obj, value)

    def post_get(self, obj: Any, value: Any) -> Any:
        return self.post_get_processing(obj, value)

    def pre_delete(self, obj: Any, value: Any) -> Any:
        return self.pre_delete_processing(obj, value)

    def post_delete(self, obj: Any, value: Any) -> Any:
        return self.post_delete_processing(obj, value)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_validation_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_set_processing(self, instance: Any, value: Any) -> Any:
        return value

    def pre_get_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_get_processing(self, instance: Any, value: Any) -> Any:
        return value

    def pre_delete_processing(self, instance: Any, value: Any) -> Any:
        return value

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        return value

    @abstractmethod
    def validate(self, instance: Any = None, value: Any = None) -> None:
        raise NotImplementedError


def check_type(owner: Any, instance: Any, value: Any) -> None:
    annotation = getattr(owner, "annotation", None)
    if annotation is not None and value is not None and not _is_instance_of(value, annotation):
        raise TypeError(
            f"{owner.name} expect {annotation} type, got {type(value).__name__} type instead"
        )


def check_required(owner: Any, instance: Any, value: Any) -> None:
    if getattr(owner, "required", None) is True and value is None:
        raise ValueError(f"{owner.name} requires value, got {value} instead")


def check_pattern(owner: Any, instance: Any, value: Any) -> None:
    pattern = getattr(owner, "pattern", None)
    if pattern is None:
        return
    source = pattern.pattern if isinstance(pattern, PatternType) else pattern
    if value is None:
        return
    text = value if isinstance(value, str) else str(value)
    if not re.compile(source).findall(text):
        label = pattern.alias if isinstance(pattern, PatternType) and pattern.alias else pattern
        raise ValueError(f"{owner.name} must have the pattern {label}")


def check_reassignment(owner: Any, instance: Any, value: Any) -> None:
    if getattr(owner, "reassign", None) is not False:
        return
    counts = getattr(owner, "_assignment_counts", {})
    if counts.get(id(instance), 0) >= 1:
        raise AttributeError(
            f"{owner.name} can be assigned only once, "
            f"attempted to reassign with value '{value}' instead"
        )


def check_multiple_of(owner: Any, instance: Any, value: Any) -> None:
    multiple_of = _bound(owner, "multiple_of")
    if multiple_of is None or value is None:
        return
    if multiple_of == 0:
        is_multiple = value == 0
    else:
        is_multiple = value % multiple_of == 0
    if not is_multiple:
        raise ValueError(
            f"{owner.name} expect the value multiple of {multiple_of}, got {value} instead"
        )


def check_min_value(owner: Any, instance: Any, value: Any) -> None:
    if value is None:
        return
    min_value = _bound(owner, "min_value")
    gt = _bound(owner, "gt")
    if min_value is not None and value < min_value:
        raise ValueError(
            f"{owner.name} expect the minimum value of {min_value}, got {value} instead"
        )
    if gt is not None and value <= gt:
        raise ValueError(
            f"{owner.name} expect a value greater than {gt}, got {value} instead"
        )


def check_max_value(owner: Any, instance: Any, value: Any) -> None:
    if value is None:
        return
    max_value = _bound(owner, "max_value")
    lt = _bound(owner, "lt")
    if max_value is not None and value > max_value:
        raise ValueError(
            f"{owner.name} expect the maximum value of {max_value}, got {value} instead"
        )
    if lt is not None and value >= lt:
        raise ValueError(
            f"{owner.name} expect a value less than {lt}, got {value} instead"
        )


def check_eq_value(owner: Any, instance: Any, value: Any) -> None:
    of_value = _bound(owner, "value")
    if of_value is not None and value is not None and value != of_value:
        raise ValueError(
            f"{owner.name} expect the value {of_value}, got {value} as value instead"
        )


def check_value(owner: Any, instance: Any, value: Any) -> None:
    check_min_value(owner, instance, value)
    check_max_value(owner, instance, value)
    check_eq_value(owner, instance, value)


def check_min_length(owner: Any, instance: Any, value: Any) -> None:
    min_length = _bound(owner, "min_length")
    if min_length is None or value is None:
        return
    value_length = len(value)
    if value_length < min_length:
        raise ValueError(
            f"{owner.name} expect the value of minimum length {min_length}, "
            f"got length {value_length} value instead"
        )


def check_max_length(owner: Any, instance: Any, value: Any) -> None:
    max_length = _bound(owner, "max_length")
    if max_length is None or value is None:
        return
    value_length = len(value)
    if value_length > max_length:
        raise ValueError(
            f"{owner.name} expect the value of maximum length {max_length}, "
            f"got length {value_length} value instead"
        )


def check_exact_length(owner: Any, instance: Any, value: Any) -> None:
    length = _bound(owner, "length")
    if length is None or value is None:
        return
    value_length = len(value)
    if value_length != length:
        raise ValueError(
            f"{owner.name} expect the value of length {length}, "
            f"got length {value_length} value instead"
        )


def check_length(owner: Any, instance: Any, value: Any) -> None:
    check_min_length(owner, instance, value)
    check_max_length(owner, instance, value)
    check_exact_length(owner, instance, value)


def check_choice(owner: Any, instance: Any, value: Any) -> None:
    in_choice = getattr(owner, "in_choice", None)
    not_in_choice = getattr(owner, "not_in_choice", None)
    if in_choice is not None and value is not None and value not in in_choice:
        raise ValueError(
            f"{owner.name} expect values in {in_choice}, got {value} as value instead"
        )
    if not_in_choice is not None and value in not_in_choice:
        raise ValueError(
            f"{owner.name} does not expect values in {not_in_choice}, "
            f"got {value} as value instead"
        )


def configure_value(
    obj: Any,
    min_value: Any,
    gt: Any,
    value: Any,
    eq: Any,
    max_value: Any,
    lt: Any,
) -> None:
    _reject_exclusive(
        max_value, lt, "max_value and lt both can't be initialized, select one"
    )
    _reject_exclusive(
        min_value, gt, "min_value and gt both can't be initialized, select one"
    )
    _reject_exclusive(value, eq, "value and eq both can't be initialized, select one")
    if value is None:
        value = eq
    label = "value" if eq is None else "eq"
    _reject_inverted(min_value, max_value, "max_value can not be less than min_value")
    _reject_inverted(gt, lt, "lt can not be less than gt")
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


def configure_length(obj: Any, min_length: Any, length: Any, max_length: Any) -> None:
    _reject_inverted(min_length, max_length, "max_length can not be less than min_length")
    if specified(min_length, length) and length < min_length:
        raise ValueError("length can not be less than min_length")
    if specified(max_length, length) and max_length < length:
        raise ValueError("length can not be more than max_length")
    obj.min_length = min_length
    obj.max_length = max_length
    obj.length = length


_PATH_OWNED_LEAVES = {
    "value": frozenset({"min_value", "max_value", "eq"}),
    "length": frozenset({"min_length", "max_length"}),
}

DEFAULT_PATH_NAMES = (
    "reassignment",
    "type",
    "required",
    "pattern",
    "multiple_of",
    "length",
    "value",
    "choice",
)


class ValidationPath:
    """Ordered unique validation concerns. Double-call / nested leaf fail closed.

    ``value`` already owns min/max/eq. ``length`` already owns min/max.
    A second ``validate()`` is a new pass — per-pass uniqueness, not process lifetime.
    """

    def __init__(self, names: Iterable[str]) -> None:
        names = tuple(names)
        seen: set[str] = set()
        for name in names:
            if name in seen:
                raise ValueError(f"validation path double-call: {name!r}")
            seen.add(name)
        for aggregate, owned in _PATH_OWNED_LEAVES.items():
            clash = seen & owned
            if aggregate in seen and clash:
                raise ValueError(
                    f"validation path conflict: {aggregate!r} already owns {sorted(clash)}"
                )
        self.names = names

    def run(
        self,
        owner: Any,
        instance: Any,
        value: Any,
        lookup: dict[str, Lookup],
    ) -> list[Any]:
        ran: set[str] = set()
        results = []
        for name in self.names:
            if name in ran:
                raise ValueError(f"validation path double-call: {name!r}")
            ran.add(name)
            results.append(lookup[name](owner, instance, value))
        return results


class TypeValidator(ValidateProperty):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_type(self, instance, value)


class RequiredValidator(ValidateProperty):
    def __init__(self, required: bool | None = None, **kwargs: Any) -> None:
        if required is not None and not isinstance(required, bool):
            raise TypeError(
                f"required expected type bool value, got {type(required).__name__} type instead"
            )
        self.required = required
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_required(self, instance, value)


class PatternValidator(ValidateProperty):
    def __init__(self, pattern: Any = None, **kwargs: Any) -> None:
        self.pattern = pattern
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_pattern(self, instance, value)


class ReassignValidator(ValidateProperty):
    def __init__(self, reassign: bool | None = None, **kwargs: Any) -> None:
        if reassign is not None and not isinstance(reassign, bool):
            raise TypeError(
                f"reassign expected type bool value, got {type(reassign).__name__} type instead"
            )
        self.reassign = reassign
        self.number_of_assignment = 0
        self._assignment_counts: dict[int, int] = {}
        super().__init__(**kwargs)

    def pre_set(self, obj: Any, value: Any) -> Any:
        self._assignment_counts.setdefault(id(obj), 0)
        return super().pre_set(obj, value)

    def post_set(self, obj: Any, value: Any) -> Any:
        self._assignment_counts[id(obj)] = self._assignment_counts.get(id(obj), 0) + 1
        self.number_of_assignment += 1
        return super().post_set(obj, value)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_reassignment(self, instance, value)


class MultipleValidator(ValidateProperty):
    def __init__(self, multiple_of: Any = None, **kwargs: Any) -> None:
        self.multiple_of = multiple_of
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_multiple_of(self, instance, value)


class MinValueValidator(ValidateProperty):
    def __init__(
        self,
        min_value: Any = None,
        gt: Any = None,
        **kwargs: Any,
    ) -> None:
        _reject_exclusive(
            min_value, gt, "min_value and gt both can't be initialized, select one"
        )
        self.min_value = min_value
        self.gt = gt
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_min_value(self, instance, value)


class MaxValueValidator(ValidateProperty):
    def __init__(
        self,
        max_value: Any = None,
        lt: Any = None,
        **kwargs: Any,
    ) -> None:
        _reject_exclusive(
            max_value, lt, "max_value and lt both can't be initialized, select one"
        )
        self.max_value = max_value
        self.lt = lt
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_max_value(self, instance, value)


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
        configure_value(self, min_value, gt, value, eq, max_value, lt)
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_value(self, instance, value)


class MinLengthValidator(ValidateProperty):
    def __init__(self, min_length: int | None = None, **kwargs: Any) -> None:
        self.min_length = min_length
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_min_length(self, instance, value)


class MaxLengthValidator(ValidateProperty):
    def __init__(self, max_length: int | None = None, **kwargs: Any) -> None:
        self.max_length = max_length
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_max_length(self, instance, value)


class LengthValidator(ValidateProperty):
    """Exact length plus inclusive min/max. Composes bound checks."""

    def __init__(
        self,
        min_length: int | None = None,
        length: int | None = None,
        max_length: int | None = None,
        **kwargs: Any,
    ) -> None:
        configure_length(self, min_length, length, max_length)
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_length(self, instance, value)


class ChoiceValidator(ValidateProperty):
    def __init__(
        self,
        in_choice: Any = None,
        not_in_choice: Any = None,
        **kwargs: Any,
    ) -> None:
        self.in_choice = in_choice
        self.not_in_choice = not_in_choice
        super().__init__(**kwargs)

    def validate(self, instance: Any = None, value: Any = None) -> None:
        check_choice(self, instance, value)


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
        **kwargs: Any,
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
        configure_value(self, min_value, gt, value, eq, max_value, lt)
        configure_length(self, min_length, length, max_length)
        self.in_choice = in_choice
        self.not_in_choice = not_in_choice
        self.cache_task = cache_task
        self._custom_validators: dict[str, list[Callable[..., Any]]] = defaultdict(list)
        self._processors: dict[str, dict[str, list[Callable[..., Any]]]] = {
            phase: defaultdict(list)
            for phase in (
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
            **kwargs,
        )

    def _unit_lookup(self) -> dict[str, Lookup]:
        return {
            "reassignment": check_reassignment,
            "type": check_type,
            "required": check_required,
            "pattern": check_pattern,
            "multiple_of": check_multiple_of,
            "length": check_length,
            "value": check_value,
            "choice": check_choice,
        }

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self.validation_path.run(self, instance, value, self._unit_lookup())
        if instance is None:
            return
        for func in self._custom_validators[instance.__class__.__name__]:
            func(instance, value)

    def add_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._custom_validators[_namespace(func, namespace)].append(func)
        return func

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        for func in self._processors[phase][instance.__class__.__name__]:
            value = func(instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        for func in self._tasks[phase][instance.__class__.__name__]:
            func(instance, value)
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

    def pre_set(self, obj: Any, value: Any) -> Any:
        self._assignment_counts.setdefault(id(obj), 0)
        return super().pre_set(obj, value)

    def post_set(self, obj: Any, value: Any) -> Any:
        self._assignment_counts[id(obj)] = self._assignment_counts.get(id(obj), 0) + 1
        self.number_of_assignment += 1
        return super().post_set(obj, value)


class IntegerValidator(Validator):
    annotation = int


class StringValidator(Validator):
    annotation = str


class BooleanValidator(Validator):
    annotation = bool
