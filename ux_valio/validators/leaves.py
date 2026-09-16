# SPDX-License-Identifier: MIT
"""Single-concern Door A leaves. Each leaf owns its validate methods."""

from __future__ import annotations

import re
import types
from collections.abc import (
    Callable as AbcCallable,
    Collection,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set as AbstractSet,
)
from typing import Annotated, Any, Literal, TypeVar, Union, get_args, get_origin

from ux_valio.pattern import PatternType
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.bounds import bound

_SEQUENCE_ORIGINS = (Sequence, MutableSequence)
_MAPPING_ORIGINS = (Mapping, MutableMapping)
_SET_ABC_ORIGINS = (AbstractSet, MutableSet)
_COLLECTION_ORIGINS = (Collection,)


def is_instance_of(value: Any, annotation: Any) -> bool:
    """Door A type honesty: origin+args recurse; unknown TypeError is False.

    ``list[int]`` is a list of ints. Parametrized args (element types,
    Literal membership, Annotated inner type) are checked. PEP 695 aliases
    unwrap ``__value__`` when present. ``typing.Any`` and an unset ``None``
    annotation accept. Callable origin is checked; signature is not.
    TypedDict is fail-closed. Not typingx. Not a public ``check_*``.
    """
    if annotation is None or annotation is Any:
        return True
    if type(annotation).__name__ == "TypeAliasType":
        inner = getattr(annotation, "__value__", None)
        if inner is None:
            return False
        return is_instance_of(value, inner)
    if isinstance(annotation, str):
        return False
    supertype = getattr(annotation, "__supertype__", None)
    if supertype is not None and get_origin(annotation) is None:
        return is_instance_of(value, supertype)
    if isinstance(annotation, TypeVar):
        if annotation.__constraints__:
            return any(is_instance_of(value, arg) for arg in annotation.__constraints__)
        if annotation.__bound__ is not None:
            return is_instance_of(value, annotation.__bound__)
        return False
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Annotated:
        if not args:
            return False
        return is_instance_of(value, args[0])
    if origin is Union or origin is types.UnionType:
        if not args:
            return True
        return any(is_instance_of(value, arg) for arg in args)
    if origin is type(None):
        return value is None
    if origin is Literal:
        return value in args
    if origin is list:
        return isinstance(value, list) and _elements_match(value, args)
    if origin is set:
        return isinstance(value, set) and _elements_match(value, args)
    if origin is frozenset:
        return isinstance(value, frozenset) and _elements_match(value, args)
    if origin is dict:
        return isinstance(value, dict) and _mapping_match(value, args)
    if origin is tuple:
        return isinstance(value, tuple) and _tuple_match(value, args)
    if origin is AbcCallable:
        return _isinstance_closed(value, origin)
    if origin in _MAPPING_ORIGINS:
        return isinstance(value, origin) and _mapping_match(value, args)
    if origin in _SET_ABC_ORIGINS:
        return isinstance(value, origin) and _elements_match(value, args)
    if origin in _SEQUENCE_ORIGINS:
        return isinstance(value, origin) and _elements_match(value, args)
    if origin in _COLLECTION_ORIGINS:
        return isinstance(value, origin) and _elements_match(value, args)
    target = origin if origin is not None else annotation
    return _isinstance_closed(value, target)


def _isinstance_closed(value: Any, target: Any) -> bool:
    try:
        return isinstance(value, target)
    except TypeError:
        return False


def _elements_match(value: Any, args: tuple[Any, ...]) -> bool:
    if not args:
        return True
    item_annotation = args[0]
    return all(is_instance_of(item, item_annotation) for item in value)


def _mapping_match(value: Any, args: tuple[Any, ...]) -> bool:
    if not args:
        return True
    if len(args) != 2:
        return False
    key_annotation, value_annotation = args
    return all(
        is_instance_of(key, key_annotation) and is_instance_of(item, value_annotation)
        for key, item in value.items()
    )


def _tuple_match(value: Any, args: tuple[Any, ...]) -> bool:
    if len(args) == 2 and args[1] is Ellipsis:
        return all(is_instance_of(item, args[0]) for item in value)
    if len(value) != len(args):
        return False
    return all(is_instance_of(item, arg) for item, arg in zip(value, args, strict=True))


class TypeValidator(ValidateProperty):
    def _validate_type(self, instance: Any, value: Any) -> None:
        annotation = getattr(self, "annotation", None)
        if annotation is not None and value is not None and not is_instance_of(value, annotation):
            raise TypeError(
                f"{self.name} expect {annotation} type, got {type(value).__name__} type instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_type(instance, value)


class RequiredValidator(ValidateProperty):
    def __init__(self, required: bool | None = None, **kwargs: Any) -> None:
        if required is not None and not isinstance(required, bool):
            raise TypeError(
                f"required expected type bool value, got {type(required).__name__} type instead"
            )
        self.required = required
        super().__init__(**kwargs)

    def _validate_required(self, instance: Any, value: Any) -> None:
        if getattr(self, "required", None) is True and value is None:
            raise ValueError(f"{self.name} requires value, got {value} instead")

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_required(instance, value)


class PatternValidator(ValidateProperty):
    def __init__(self, pattern: Any = None, **kwargs: Any) -> None:
        self.pattern = pattern
        super().__init__(**kwargs)

    def _validate_pattern(self, instance: Any, value: Any) -> None:
        pattern = getattr(self, "pattern", None)
        if pattern is None:
            return
        source = pattern.pattern if isinstance(pattern, PatternType) else pattern
        if value is None:
            return
        text = value if isinstance(value, str) else str(value)
        if not re.compile(source).findall(text):
            label = pattern.alias if isinstance(pattern, PatternType) and pattern.alias else pattern
            raise ValueError(f"{self.name} must have the pattern {label}")

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_pattern(instance, value)


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

    def notify_pre_set(self, obj: Any) -> None:
        self._assignment_counts.setdefault(id(obj), 0)

    def notify_post_set(self, obj: Any) -> None:
        self._assignment_counts[id(obj)] = self._assignment_counts.get(id(obj), 0) + 1
        self.number_of_assignment += 1

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        self._assignment_counts.pop(id(instance), None)
        return value

    def _validate_reassignment(self, instance: Any, value: Any) -> None:
        if getattr(self, "reassign", None) is not False:
            return
        counts = getattr(self, "_assignment_counts", {})
        if counts.get(id(instance), 0) >= 1:
            raise AttributeError(
                f"{self.name} can be assigned only once, "
                f"attempted to reassign with value '{value}' instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_reassignment(instance, value)


class MultipleValidator(ValidateProperty):
    def __init__(self, multiple_of: Any = None, **kwargs: Any) -> None:
        self.multiple_of = multiple_of
        super().__init__(**kwargs)

    def _validate_multiple_of(self, instance: Any, value: Any) -> None:
        multiple_of = bound(self, "multiple_of")
        if multiple_of is None or value is None:
            return
        if multiple_of == 0:
            is_multiple = value == 0
        else:
            is_multiple = value % multiple_of == 0
        if not is_multiple:
            raise ValueError(
                f"{self.name} expect the value multiple of {multiple_of}, got {value} instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_multiple_of(instance, value)


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

    def _validate_choice(self, instance: Any, value: Any) -> None:
        in_choice = getattr(self, "in_choice", None)
        not_in_choice = getattr(self, "not_in_choice", None)
        if in_choice is not None and value is not None and value not in in_choice:
            raise ValueError(
                f"{self.name} expect values in {in_choice}, got {value} as value instead"
            )
        if not_in_choice is not None and value in not_in_choice:
            raise ValueError(
                f"{self.name} does not expect values in {not_in_choice}, "
                f"got {value} as value instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_choice(instance, value)
