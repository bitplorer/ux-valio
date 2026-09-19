# SPDX-License-Identifier: MIT
"""Single-concern validator leaves. Each leaf owns its validate methods."""

from __future__ import annotations

import re
import types
import typing
import weakref
from collections.abc import (
    Callable as AbcCallable,
    Collection,
    Container,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    Set as AbstractSet,
)
from typing import Annotated, Any, Literal, TypeVar, Union, get_args, get_origin, get_type_hints, is_typeddict

from ux_valio.errors import continue_or_raise, raise_collected
from ux_valio.pattern import PatternType
from ux_valio.validators.base import ValidateProperty, _register_annotation_checker
from ux_valio.validators.bounds import read_bound

_TYPED_DICT_QUALIFIERS = tuple(
    qualifier
    for qualifier in (
        getattr(typing, "Required", None),
        getattr(typing, "NotRequired", None),
        getattr(typing, "ReadOnly", None),
    )
    if qualifier is not None
)
_TYPE_ALIAS_TYPE = getattr(typing, "TypeAliasType", None)


def _peel_annotation(annotation: Any) -> Any:

    if _TYPE_ALIAS_TYPE is not None and isinstance(annotation, _TYPE_ALIAS_TYPE):
        inner = getattr(annotation, "__value__", None)
        return _PeelFail if inner is None else inner
    supertype = getattr(annotation, "__supertype__", None)
    if supertype is not None and get_origin(annotation) is None:
        return supertype
    return annotation


class _PeelFailType:
    __slots__ = ()


_PeelFail = _PeelFailType()


def _check_annotated(value: Any, args: tuple[Any, ...]) -> bool:
    return bool(args) and is_instance_of(value, args[0])


def _check_union(value: Any, args: tuple[Any, ...]) -> bool:
    return True if not args else any(is_instance_of(value, arg) for arg in args)


def _check_none(value: Any, args: tuple[Any, ...]) -> bool:
    return value is None


def _check_literal(value: Any, args: tuple[Any, ...]) -> bool:
    return value in args


def _check_callable(value: Any, args: tuple[Any, ...]) -> bool:
    return _isinstance_closed(value, AbcCallable)


def _exact_type(typ: type, matcher: Any):
    """``isinstance(value, typ)`` then the same-shape matcher."""

    def check(value: Any, args: tuple[Any, ...]) -> bool:
        return isinstance(value, typ) and matcher(value, args)

    return check


def _isinstance_closed(value: Any, target: Any) -> bool:
    try:
        return isinstance(value, target)
    except TypeError:
        return False


def _elements_match(value: Any, args: tuple[Any, ...]) -> bool:
    if not args:
        return True
    return all(is_instance_of(item, args[0]) for item in value)


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


# Type-door tables live next to ``is_instance_of``, not on ``TypeValidator``.
_ORIGIN_CHECKERS = {
    Annotated: _check_annotated,
    Union: _check_union,
    types.UnionType: _check_union,
    type(None): _check_none,
    Literal: _check_literal,
    list: _exact_type(list, _elements_match),
    set: _exact_type(set, _elements_match),
    frozenset: _exact_type(frozenset, _elements_match),
    dict: _exact_type(dict, _mapping_match),
    tuple: _exact_type(tuple, _tuple_match),
    AbcCallable: _check_callable,
}

_ORIGIN_GROUPS = (
    ((Mapping, MutableMapping), _mapping_match),
    ((AbstractSet, MutableSet), _elements_match),
    ((Sequence, MutableSequence), _elements_match),
    ((Collection,), _elements_match),
)


def is_instance_of(value: Any, annotation: Any) -> bool:
    """Value vs annotation at set. Twin of ``is_subclass_of`` (bind)."""
    if annotation is None or annotation is Any:
        return True
    # Concrete classes (int, str, Enum) skip peel / origin tables.
    if isinstance(annotation, type) and get_origin(annotation) is None:
        if is_typeddict(annotation):
            return _typed_dict_match(value, annotation)
        return _isinstance_closed(value, annotation)
    peeled = _peel_annotation(annotation)
    if peeled is _PeelFail:
        return False
    if peeled is not annotation:
        return is_instance_of(value, peeled)
    if isinstance(annotation, str):
        return False
    if isinstance(annotation, TypeVar):
        if annotation.__constraints__:
            return any(is_instance_of(value, arg) for arg in annotation.__constraints__)
        if annotation.__bound__ is not None:
            return is_instance_of(value, annotation.__bound__)
        return False
    origin = get_origin(annotation)
    args = get_args(annotation)
    checker = _ORIGIN_CHECKERS.get(origin)
    if checker is not None:
        return checker(value, args)
    for group, matcher in _ORIGIN_GROUPS:
        if origin in group:
            return isinstance(value, origin) and matcher(value, args)
    target = origin if origin is not None else annotation
    if is_typeddict(target):
        return _typed_dict_match(value, target)
    return _isinstance_closed(value, target)


def _unwrap_field_annotation(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    """Peel ``Annotated`` and TypedDict qualifiers. Keep validator extras.

    Presence is ``TypedDict.__required_keys__`` (the metaclass), not this
    peel. This only exposes the store type and ``Annotated`` metadata.
    """
    extras: list[Any] = []
    while True:
        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation)
            annotation = args[0] if args else annotation
            extras.extend(args[1:])
            continue
        if origin in _TYPED_DICT_QUALIFIERS:
            args = get_args(annotation)
            annotation = args[0] if args else annotation
            continue
        return annotation, tuple(extras)


def _annotated_store_type(annotation: Any) -> Any:
    return _unwrap_field_annotation(annotation)[0]


def _typed_dict_match(value: Any, annotation: Any) -> bool:
    """Mapping vs TypedDict using the metaclass keys, not a second parser.

    ``__required_keys__`` is what ``total=`` / ``Required`` / ``NotRequired``
    already computed. Extra keys fail-closed. Value types peel qualifiers
    then ``is_instance_of``.
    """
    if not isinstance(value, Mapping) or isinstance(value, (str, bytes)):
        return False
    try:
        hints = get_type_hints(annotation, include_extras=True)
    except Exception:
        return False
    required = getattr(annotation, "__required_keys__", frozenset(hints))
    keys = frozenset(value)
    if not required <= keys:
        return False
    extra = keys - frozenset(hints)
    extra_items = getattr(annotation, "__extra_items__", None)
    closed = getattr(annotation, "__closed__", None)
    if extra:
        if extra_items is not None and extra_items is not type(None):
            if not all(is_instance_of(value[key], extra_items) for key in extra):
                return False
        elif closed is False:
            pass
        else:
            return False
    for key, field_ann in hints.items():
        if key not in value:
            continue
        if not is_instance_of(value[key], _annotated_store_type(field_ann)):
            return False
    return True


def _typed_dict_key_validators(schema: Any, key: str, field_ann: Any) -> tuple[Any, ...]:
    """Class-body field default, then ``Annotated`` extras. One object once."""
    found: list[Any] = []
    attr = schema.__dict__.get(key)
    if isinstance(attr, ValidateProperty):
        found.append(attr)
    for extra in _unwrap_field_annotation(field_ann)[1]:
        if isinstance(extra, ValidateProperty) and extra is not attr:
            found.append(extra)
    return tuple(found)


def _validate_typed_dict(owner: Any, value: Any, annotation: Any = None) -> None:
    """Run key validators on a TypedDict mapping.

    ``name: str = StringValidator()`` on the TypedDict is the same default
    as a dataclass field: ``type`` calls ``__set_name__``, so ``_owner``
    is that class. ``pre_set`` write-back then ``post_set``. ``self`` in
    those hooks is the mapping.
    """
    if annotation is None:
        annotation = getattr(owner, "annotation", None)
    if annotation is None or value is None:
        return
    peeled = _peel_annotation(annotation)
    if peeled is _PeelFail:
        return
    annotation = _annotated_store_type(peeled)
    if not is_typeddict(annotation) or not isinstance(value, Mapping):
        return
    try:
        hints = get_type_hints(annotation, include_extras=True)
    except Exception:
        return
    errors: list[BaseException] = []
    collect = getattr(owner, "collect_all", True)
    prefix = getattr(owner, "name", None)
    for key, field_ann in hints.items():
        if key not in value:
            continue
        item = value[key]
        for extra in _typed_dict_key_validators(annotation, key, field_ann):
            # Errors name ``person.email``; restore so a shared descriptor
            # keeps the bind name from ``__set_name__``.
            previous_name = extra.name
            extra.name = f"{prefix}.{key}" if prefix else key
            try:
                new_item = extra._run_pre_set(value, item)
                if isinstance(value, MutableMapping):
                    value[key] = new_item
                extra._run_post_set(value, new_item)
                item = new_item
            except Exception as err:
                continue_or_raise(collect, errors, err)
            finally:
                extra.name = previous_name
        nested = _annotated_store_type(field_ann)
        if is_typeddict(nested):
            nested_value = value[key] if key in value else item
            try:
                _validate_typed_dict(owner, nested_value, nested)
            except Exception as err:
                continue_or_raise(collect, errors, err)
    raise_collected(errors, name=prefix)


class TypeValidator(ValidateProperty):
    """Single-concern type door. ``is_instance_of`` owns the origin tables."""

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
        self._compiled: re.Pattern[Any] | None = None
        self._compiled_source: Any = object()
        super().__init__(**kwargs)

    def _compiled_finder(self: Any, source: str | bytes) -> re.Pattern[Any]:

        compiled = getattr(self, "_compiled", None)
        if compiled is not None and source == getattr(self, "_compiled_source", object()):
            return compiled
        compiled = re.compile(source)
        self._compiled = compiled
        self._compiled_source = source
        return compiled

    def _validate_pattern(self, instance: Any, value: Any) -> None:
        pattern = getattr(self, "pattern", None)
        if pattern is None:
            return
        source = pattern.pattern if isinstance(pattern, PatternType) else pattern
        if value is None:
            return
        if isinstance(source, bytes):
            if not isinstance(value, bytes):
                raise TypeError(
                    f"{self.name} expects bytes to match a bytes pattern, "
                    f"got {type(value).__name__} type instead"
                )
            matched: str | bytes = value
        elif isinstance(source, str):
            if not isinstance(value, str):
                raise TypeError(
                    f"{self.name} expects str to match a str pattern, "
                    f"got {type(value).__name__} type instead"
                )
            matched = value
        else:
            raise TypeError(
                f"{self.name} pattern must be str or bytes, "
                f"got {type(source).__name__} type instead"
            )
        if not PatternValidator._compiled_finder(self, source).findall(matched):
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
        self._assignment_alive: dict[int, weakref.ref[Any]] = {}
        super().__init__(**kwargs)

    def _watch_assignment(self: Any, obj: Any) -> int:

        oid = id(obj)

        def _drop(_ref: Any, key: int = oid) -> None:
            self._assignment_counts.pop(key, None)
            self._assignment_alive.pop(key, None)

        try:
            self._assignment_alive[oid] = weakref.ref(obj, _drop)
        except TypeError:
            pass
        return oid

    def _notify_pre_set(self: Any, obj: Any) -> None:
        self._assignment_counts.setdefault(self._watch_assignment(obj), 0)

    def _notify_post_set(self: Any, obj: Any) -> None:
        oid = self._watch_assignment(obj)
        self._assignment_counts[oid] = self._assignment_counts.get(oid, 0) + 1
        self.number_of_assignment += 1

    def _post_delete(self: Any, instance: Any, value: Any) -> Any:
        oid = id(instance)
        self._assignment_counts.pop(oid, None)
        self._assignment_alive.pop(oid, None)
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
        multiple_of = read_bound(self, "multiple_of")
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
        type(self)._reject_non_container("in_choice", in_choice)
        type(self)._reject_non_container("not_in_choice", not_in_choice)
        super().__init__(**kwargs)

    @staticmethod
    def _reject_non_container(label: str, bag: Any) -> None:
        """Choice bags must support ``in``. ``None`` is unspecified."""
        if bag is None:
            return
        if not isinstance(bag, Container):
            raise TypeError(
                f"{label} expected a container, got {type(bag).__name__} type instead"
            )

    def _validate_choice(self, instance: Any, value: Any) -> None:
        in_choice = getattr(self, "in_choice", None)
        not_in_choice = getattr(self, "not_in_choice", None)
        if in_choice is not None and value is not None and value not in in_choice:
            raise ValueError(
                f"{self.name} expect values in {in_choice}, got {value} as value instead"
            )
        if not_in_choice is not None and value is not None and value in not_in_choice:
            raise ValueError(
                f"{self.name} does not expect values in {not_in_choice}, "
                f"got {value} as value instead"
            )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._validate_choice(instance, value)


_register_annotation_checker(is_instance_of)
