# SPDX-License-Identifier: MIT
"""Descriptor that validates in ``pre_set`` before store.

``ValidateProperty`` is the Door A unit. Concern leaves and facades subclass
it once — they do not multiple-inherit each other. Validator objects compose
with ``&`` / ``|`` (AllOf / AnyOf) or explicit ``AllOf`` / ``AnyOf``.
``Chain`` is ``AllOf``. Hang ``add_*`` on ``Validator`` or the compose root.

``&`` / ``|`` use compose classes bound once. ``compose.py`` fills the cache
at import so the operator hot path does not import. A direct
``from ux_valio.validators.base`` import still loads on first ``&`` / ``|``.
``leaves.py`` binds ``is_instance_of`` the same way for the store type door.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from ux_valio.descriptor import Property

if TYPE_CHECKING:
    from ux_valio.validators.compose import AllOf, AnyOf

# Filled once by ``_register_compose_types`` (compose import) or by the
# first operator use. Not a public dial.
_AllOf: type | None = None
_AnyOf: type | None = None
_compose_types: tuple[type, type] | None = None
_matches_annotation = None


def _register_compose_types(allof: type, anyof: type) -> None:
    """Bind AllOf / AnyOf once. ``compose.py`` calls this at import."""
    global _AllOf, _AnyOf, _compose_types
    _AllOf = allof
    _AnyOf = anyof
    _compose_types = (allof, anyof)


def _load_compose_types() -> tuple[type, type]:
    """Return ``(AllOf, AnyOf)``, loading compose at most once."""
    if _compose_types is None:
        from ux_valio.validators.compose import AllOf, AnyOf

        _register_compose_types(AllOf, AnyOf)
    assert _compose_types is not None
    return _compose_types


def _register_annotation_checker(checker: Any) -> None:
    """Bind ``is_instance_of`` once. ``leaves.py`` calls this at import."""
    global _matches_annotation
    _matches_annotation = checker


def _annotation_accepts(annotation: Any, value: Any) -> bool:
    """Type-door membership. Loads ``is_instance_of`` at most once."""
    if _matches_annotation is None:
        from ux_valio.validators.leaves import is_instance_of

        _register_annotation_checker(is_instance_of)
    checker = _matches_annotation
    if checker is None:
        raise TypeError("type-door checker is not bound")
    return checker(value, annotation)


class ValidateProperty(Property, ABC):
    """Descriptor that validates in ``pre_set`` before store."""

    def pre_set(self, obj: Any, value: Any) -> Any:
        self.notify_pre_set(obj)
        value = self.pre_validation_processing(obj, value)
        self.validate(instance=obj, value=value)
        value = self.post_validation_processing(obj, value)
        self._reject_store_type_mismatch(value)
        self._reject_store_identity(value)
        return value

    def _reject_store_type_mismatch(self, value: Any) -> None:
        """Annotation is a store invariant: post_validate cannot smuggle a bad type.

        Untyped ``Validator()`` (annotation None) does not gate. ``None`` stays
        skip, same as the type path. Custom validators are not re-run.
        """
        annotation = getattr(self, "annotation", None)
        if annotation is None or value is None:
            return
        if not _annotation_accepts(annotation, value):
            raise TypeError(
                f"{self.name} expect {annotation} type, got {type(value).__name__} type instead"
            )

    def _reject_store_identity(self, value: Any) -> None:
        """Named-facade extra is a store invariant: post_validate cannot smuggle a lie.

        Type door is ``_reject_store_type_mismatch``. This runs the facade's
        ``_validate_named_facade`` on the to-store value. Custom validators
        and path bounds are not re-run. Untyped / unnamed descriptors no-op.
        """
        extra = getattr(self, "_validate_named_facade", None)
        if extra is None:
            return
        extra(None, value)

    def post_set(self, obj: Any, value: Any) -> Any:
        self.notify_post_set(obj)
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

    def notify_pre_set(self, obj: Any) -> None:
        """Lifecycle hook for composition; default no-op."""

    def notify_post_set(self, obj: Any) -> None:
        """Lifecycle hook for composition; default no-op."""

    def __and__(self, other: object) -> AllOf:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        allof, _anyof = _load_compose_types()
        return allof(self, other)

    def __or__(self, other: object) -> AnyOf:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        _allof, anyof = _load_compose_types()
        return anyof(self, other)

    @abstractmethod
    def validate(self, instance: Any = None, value: Any = None) -> None:
        raise NotImplementedError
