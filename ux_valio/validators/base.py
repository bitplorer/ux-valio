# SPDX-License-Identifier: MIT
"""Descriptor that validates in ``pre_set`` before store.

``ValidateProperty`` is the unit. Concern leaves and facades subclass it
once — they do not multiple-inherit each other. ``&`` / ``|`` (and
``AllOf`` / ``AnyOf``) live here: they *are* those operators. ``Chain``
is ``AllOf``. ``pre_validate`` / ``task_*`` live on ``ValidateProperty`` — hang on the
field default, leaf or facade.

``leaves.py`` binds ``is_instance_of`` once for the store type door.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, TypeVar, get_origin, is_typeddict

from ux_valio.descriptor import Property, _Opts, _UNSET, is_subclass_of
from ux_valio.errors import ValidationErrors, raise_collected, run_steps
from ux_valio.validators.hooks import HookHost

T = TypeVar("T")

_matches_annotation = None


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


class ValidateProperty(HookHost, Property[T], ABC):
    """Descriptor that validates in ``_run_pre_set`` before store.

    ``ValidateProperty[int]`` / ``Validator[int]`` is the stored-type
    subscript. It fills ``annotation`` when the class did not declare one.
    ``pre_validate`` / ``task_*`` and the processor registries come from ``HookHost``.

    Type checkers: construction is ``Any`` so ``name: str = StringValidator()``
    and ``owner: User = UserValidator()`` both assign. Runtime the object is
    still this descriptor. mypy honors this via ``ux_valio.mypy_plugin``.
    """

    if TYPE_CHECKING:
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...

    def _run_pre_set(self, obj: Any, value: Any) -> Any:
        self._take_subscript_annotation()
        self._notify_pre_set(obj)
        value = self._pre_validate(obj, value)
        self.validate(instance=obj, value=value)
        value = self._post_validate(obj, value)
        self._reject_store_type_mismatch(value)
        self._reject_store_identity(value)
        return value

    def _validate_type(self, instance: Any, value: Any) -> None:
        self._take_subscript_annotation()
        annotation = getattr(self, "annotation", None)
        if annotation is not None and value is not None and not _annotation_accepts(
            annotation, value
        ):
            raise TypeError(
                f"{self.name} expect {annotation} type, got {type(value).__name__} type instead"
            )
        if (
            isinstance(annotation, type)
            and get_origin(annotation) is None
            and not is_typeddict(annotation)
        ):
            return
        from ux_valio.validators.leaves import _validate_typed_dict

        _validate_typed_dict(self, value)

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

    def _run_post_set(self, obj: Any, value: Any) -> Any:
        self._notify_post_set(obj)
        return self._post_set(obj, value)

    def _run_pre_get(self, obj: Any, value: Any) -> Any:
        return self._pre_get(obj, value)

    def _run_post_get(self, obj: Any, value: Any) -> Any:
        return self._post_get(obj, value)

    def _run_pre_delete(self, obj: Any, value: Any) -> Any:
        return self._pre_delete(obj, value)

    def _run_post_delete(self, obj: Any, value: Any) -> Any:
        return self._post_delete(obj, value)

    def _notify_pre_set(self, obj: Any) -> None:
        """Lifecycle hook for composition; default no-op."""

    def _notify_post_set(self, obj: Any) -> None:
        """Lifecycle hook for composition; default no-op."""

    def __and__(self, other: object) -> Any:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        return AllOf(self, other)

    def __or__(self, other: object) -> Any:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        return AnyOf(self, other)

    @abstractmethod
    def validate(self, instance: Any = None, value: Any = None) -> None:
        raise NotImplementedError


class _Of(ValidateProperty):
    """AllOf / AnyOf share flatten, specified-theory merge, and member order."""

    validators: tuple[ValidateProperty, ...]
    _merge_member_annotations = True
    _propagate_annotation = True

    def __init__(
        self,
        *validators: ValidateProperty,
        name: str | None = None,
        default: Any = None,
        default_factory: Any = None,
        doc: str | None = None,
        debug: bool | None = None,
        logger: Any = _UNSET,
        collect_all: Any = _UNSET,
        **kwargs: Any,
    ) -> None:
        self.validators = type(self)._flatten(type(self)._as_validators(validators))
        if type(self)._merge_member_annotations:
            annotation = type(self)._merged_annotation(self.validators)
            if annotation is not None:
                self.annotation = annotation
        merged = _Opts.merge(*(item._opts for item in self.validators)).overlay(
            debug=debug,
            default=default,
            default_factory=default_factory,
            doc=doc,
            logger=logger,
            collect_all=collect_all,
        )
        super().__init__(name=name, _opts=merged, **kwargs)

    @staticmethod
    def _as_validators(parts: Iterable[Any]) -> tuple[ValidateProperty, ...]:
        validators = tuple(parts)
        if len(validators) < 2:
            raise TypeError("composition requires at least two validators")
        for item in validators:
            if not isinstance(item, ValidateProperty):
                raise TypeError(
                    f"expected ValidateProperty, got {type(item).__name__} instead"
                )
        return validators

    @staticmethod
    def _keep_nested(item: Any) -> bool:
        if not isinstance(item, _Of):
            return False
        if HookHost._has_hooks(item):
            return True
        members = _Opts.merge(*(member._opts for member in item.validators))
        return item._opts.keeps_nesting(members)

    @classmethod
    def _flatten(cls, parts: Iterable[ValidateProperty]) -> tuple[ValidateProperty, ...]:
        out: list[ValidateProperty] = []
        for item in parts:
            if type(item) is cls and not cls._keep_nested(item):
                out.extend(item.validators)
            else:
                out.append(item)
        return tuple(out)

    @staticmethod
    def _merged_annotation(validators: tuple[ValidateProperty, ...]) -> Any:
        chosen: Any = None
        for item in validators:
            annotation = getattr(item, "annotation", None)
            if annotation is None:
                continue
            if chosen is None:
                chosen = annotation
                continue
            if not is_subclass_of(annotation, chosen):
                raise TypeError(
                    "composed validators have conflicting annotations: "
                    f"{chosen!r} vs {annotation!r}"
                )
        return chosen

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)
        propagate = type(self)._propagate_annotation
        for item in self.validators:
            if item.name is None:
                item.name = self.name
            if propagate and item.annotation is None and self.annotation is not None:
                item.annotation = self.annotation

    def _notify_pre_set(self, obj: Any) -> None:
        for item in self.validators:
            item._notify_pre_set(obj)

    def _notify_post_set(self, obj: Any) -> None:
        for item in self.validators:
            item._notify_post_set(obj)

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        value = self._process_then_tasks("pre_validate", instance, value)
        for item in self.validators:
            value = item._pre_validate(instance, value)
        return value

    def _post_validate(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item._post_validate(instance, value)
        return self._process_then_tasks("post_validate", instance, value)

    def _post_set(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item._post_set(instance, value)
        return self._process_then_tasks("post_set", instance, value)

    def _pre_get(self, instance: Any, value: Any) -> Any:
        value = self._process_then_tasks("pre_get", instance, value)
        for item in self.validators:
            value = item._pre_get(instance, value)
        return value

    def _post_get(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item._post_get(instance, value)
        return self._process_then_tasks("post_get", instance, value)

    def _pre_delete(self, instance: Any, value: Any) -> Any:
        value = self._process_then_tasks("pre_delete", instance, value)
        for item in self.validators:
            value = item._pre_delete(instance, value)
        return value

    def _post_delete(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item._post_delete(instance, value)
        return self._process_then_tasks("post_delete", instance, value)


class AllOf(_Of):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        run_steps(
            (
                lambda: self._validate_type(instance, value),
                *(
                    (lambda item=item: item.validate(instance=instance, value=value))
                    for item in self.validators
                ),
                lambda: self._run_custom_validators(instance, value),
            ),
            self.collect_all,
            self.name,
        )

    def _reject_store_identity(self, value: Any) -> None:
        """Each member named extra is an AND identity. Path bounds are not re-run."""
        super()._reject_store_identity(value)
        for item in self.validators:
            extra = getattr(item, "_validate_named_facade", None)
            if extra is not None:
                extra(None, value)


Chain = AllOf


class AnyOf(_Of):
    _merge_member_annotations = False
    _propagate_annotation = False

    def _match_one_alternative(self, instance: Any, value: Any) -> None:
        """Succeed when one member validates. Else none-of-the-alternatives."""
        alt_errors: list[BaseException] = []
        for item in self.validators:
            try:
                item.validate(instance=instance, value=value)
                return
            except Exception as err:
                if isinstance(err, ValidationErrors):
                    alt_errors.extend(err.errors)
                else:
                    alt_errors.append(err)
        if self.collect_all and alt_errors:
            raise_collected(alt_errors, name=self.name)
        label = self.name if self.name is not None else type(self).__name__
        raise ValueError(f"{label} matched none of the alternatives") from (
            alt_errors[-1] if alt_errors else None
        )

    def validate(self, instance: Any = None, value: Any = None) -> None:
        self._match_one_alternative(instance, value)
        run_steps(
            (lambda: self._run_custom_validators(instance, value),),
            self.collect_all,
            self.name,
        )

    def _reject_store_identity(self, value: Any) -> None:
        """Stored value must still match one alternative.

        ``instance is None`` skips member custom validators. Path bounds on
        members are the alternatives.
        """
        super()._reject_store_identity(value)
        self._match_one_alternative(None, value)
