# SPDX-License-Identifier: MIT
"""Validator↔validator composition: AllOf / AnyOf / Chain as one Door A descriptor.

Facades do not multiple-inherit concern leaves. ``&`` / ``|`` stacks validator
*objects* into one descriptor. That is not the same as inheritance hygiene.
"""

from __future__ import annotations

from typing import Any, Iterable

from ux_valio.descriptor import _annotations_agree
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.leaves import TypeValidator


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


def _flatten(cls: type, parts: Iterable[ValidateProperty]) -> tuple[ValidateProperty, ...]:
    out: list[ValidateProperty] = []
    for item in parts:
        if type(item) is cls:
            out.extend(item.validators)  # type: ignore[attr-defined]
        else:
            out.append(item)
    return tuple(out)


def _bind_compose_kwargs(
    validators: tuple[ValidateProperty, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    left = validators[0]
    kwargs.setdefault("debug", left.debug)
    kwargs.setdefault("logger", left.logger)
    kwargs.setdefault("default", left.default)
    kwargs.setdefault("doc", left.doc)
    return kwargs


def _compose_annotation(validators: tuple[ValidateProperty, ...]) -> Any:
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


class _Compose(ValidateProperty):
    """Shared Door A descriptor for stacked validators."""

    validators: tuple[ValidateProperty, ...]

    def __init__(self, *validators: ValidateProperty, **kwargs: Any) -> None:
        self.validators = _flatten(type(self), _as_validators(validators))
        annotation = _compose_annotation(self.validators)
        if annotation is not None:
            self.annotation = annotation
        super().__init__(**_bind_compose_kwargs(self.validators, kwargs))

    def __set_name__(self, owner: type, name: str) -> None:
        super().__set_name__(owner, name)
        for item in self.validators:
            if item.name is None:
                item.name = self.name
            if item.annotation is None and self.annotation is not None:
                item.annotation = self.annotation

    def notify_pre_set(self, obj: Any) -> None:
        for item in self.validators:
            item.notify_pre_set(obj)

    def notify_post_set(self, obj: Any) -> None:
        for item in self.validators:
            item.notify_post_set(obj)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.pre_validation_processing(instance, value)
        return value

    def post_validation_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_validation_processing(instance, value)
        return value

    def post_set_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_set_processing(instance, value)
        return value

    def pre_get_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.pre_get_processing(instance, value)
        return value

    def post_get_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_get_processing(instance, value)
        return value

    def pre_delete_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.pre_delete_processing(instance, value)
        return value

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        for item in self.validators:
            value = item.post_delete_processing(instance, value)
        return value


class AllOf(_Compose):
    """AND composition: every member must validate. One Door A descriptor."""

    def validate(self, instance: Any = None, value: Any = None) -> None:
        TypeValidator._validate_type(self, instance, value)
        for item in self.validators:
            item.validate(instance=instance, value=value)


class Chain(AllOf):
    """Ordered AllOf — members validate left to right as one descriptor."""


class AnyOf(_Compose):
    """OR composition: the first member that validates wins."""

    def validate(self, instance: Any = None, value: Any = None) -> None:
        TypeValidator._validate_type(self, instance, value)
        errors: list[BaseException] = []
        for item in self.validators:
            try:
                item.validate(instance=instance, value=value)
                return
            except Exception as err:
                errors.append(err)
        label = self.name if self.name is not None else type(self).__name__
        raise ValueError(f"{label} matched none of the alternatives") from (
            errors[-1] if errors else None
        )
