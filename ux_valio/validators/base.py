# SPDX-License-Identifier: MIT
"""Descriptor that validates in ``pre_set`` before store.

``ValidateProperty`` is the unit. Concern leaves and facades subclass it
once — they do not multiple-inherit each other. ``&`` / ``|`` (and
``AllOf`` / ``AnyOf``) live here: they *are* those operators. ``Chain``
is ``AllOf``. Hang ``add_*`` on ``Validator`` or the AllOf / AnyOf root.

``leaves.py`` binds ``is_instance_of`` once for the store type door.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, TypeVar

from ux_valio.descriptor import Property, _Opt, _annotations_agree
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


class ValidateProperty(Property[T], ABC):
    """Descriptor that validates in ``pre_set`` before store.

    ``ValidateProperty[int]`` / ``Validator[int]`` is the stored-type
    subscript. It fills ``annotation`` when the class did not declare one.
    """

    def pre_set(self, obj: Any, value: Any) -> Any:
        self._take_subscript_annotation()
        self.notify_pre_set(obj)
        value = self.pre_validation_processing(obj, value)
        self.validate(instance=obj, value=value)
        value = self.post_validation_processing(obj, value)
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
        return AllOf(self, other)

    def __or__(self, other: object) -> AnyOf:
        if not isinstance(other, ValidateProperty):
            return NotImplemented
        return AnyOf(self, other)

    @abstractmethod
    def validate(self, instance: Any = None, value: Any = None) -> None:
        raise NotImplementedError


class _Of(HookHost, ValidateProperty):
    """AllOf / AnyOf share flatten, specified-theory merge, and member order."""

    validators: tuple[ValidateProperty, ...]
    _merge_member_annotations = True
    _propagate_annotation = True

    def __init__(self, *validators: ValidateProperty, **kwargs: Any) -> None:
        self.validators = type(self)._flatten(type(self)._as_validators(validators))
        if type(self)._merge_member_annotations:
            annotation = type(self)._merged_annotation(self.validators)
            if annotation is not None:
                self.annotation = annotation
        super().__init__(**type(self)._bind_kwargs(self.validators, kwargs))

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
    def _merged_attr(validators: tuple[Any, ...], attr: str, unspecified: Any) -> Any:
        merged = _Opt.merge(attr, *(_Opt.read(item, attr, unspecified) for item in validators))
        return merged.value if merged.specified else unspecified

    @staticmethod
    def _keep_nested(item: Any) -> bool:
        if not isinstance(item, _Of):
            return False
        if HookHost.has_hooks(item):
            return True
        members = item.validators
        for attr, unspecified in (
            ("debug", None),
            ("default", None),
            ("default_factory", None),
            ("doc", None),
            ("logger", False),
            ("collect_all", False),
        ):
            item_opt = _Opt.read(item, attr, unspecified)
            members_opt = _Opt.merge(
                attr, *(_Opt.read(member, attr, unspecified) for member in members)
            )
            if item_opt.specified and not members_opt.specified:
                return True
            if item_opt.specified and item_opt.value != members_opt.value:
                return True
            if not item_opt.specified and members_opt.specified:
                continue
            if item_opt.value != members_opt.value:
                return True
        return False

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
    def _bind_kwargs(
        validators: tuple[ValidateProperty, ...], kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        kwargs.setdefault("debug", _Of._merged_attr(validators, "debug", None))
        kwargs.setdefault("default", _Of._merged_attr(validators, "default", None))
        kwargs.setdefault(
            "default_factory", _Of._merged_attr(validators, "default_factory", None)
        )
        kwargs.setdefault("doc", _Of._merged_attr(validators, "doc", None))
        logger_opt = _Opt.merge(
            "logger", *(_Opt.read(item, "logger", False) for item in validators)
        )
        if "logger" not in kwargs and logger_opt.specified:
            kwargs["logger"] = logger_opt.value
        collect_opt = _Opt.merge(
            "collect_all", *(_Opt.read(item, "collect_all", False) for item in validators)
        )
        if "collect_all" not in kwargs and collect_opt.specified:
            kwargs["collect_all"] = collect_opt.value
        return kwargs

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
            if not _annotations_agree(chosen, annotation):
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

    def notify_pre_set(self, obj: Any) -> None:
        for item in self.validators:
            item.notify_pre_set(obj)

    def notify_post_set(self, obj: Any) -> None:
        for item in self.validators:
            item.notify_post_set(obj)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        value = self._process_then_tasks("pre_validate", instance, value)
        for item in self.validators:
            value = item.pre_validation_processing(instance, value)
        return value

    def post_validation_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_validation_processing(instance, value)
        return self._process_then_tasks("post_validate", instance, value)

    def post_set_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_set_processing(instance, value)
        return self._process_then_tasks("post_set", instance, value)

    def pre_get_processing(self, instance: Any, value: Any) -> Any:
        value = self._process_then_tasks("pre_get", instance, value)
        for item in self.validators:
            value = item.pre_get_processing(instance, value)
        return value

    def post_get_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_get_processing(instance, value)
        return self._process_then_tasks("post_get", instance, value)

    def pre_delete_processing(self, instance: Any, value: Any) -> Any:
        value = self._process_then_tasks("pre_delete", instance, value)
        for item in self.validators:
            value = item.pre_delete_processing(instance, value)
        return value

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_delete_processing(instance, value)
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
