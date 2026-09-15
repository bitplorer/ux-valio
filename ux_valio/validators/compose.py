# SPDX-License-Identifier: MIT
"""Validator↔validator composition: AllOf / AnyOf as one Door A descriptor.

Facades do not multiple-inherit concern leaves. ``&`` / ``|`` stacks validator
*objects* into one descriptor. Hang ``add_*`` on this compose *root*, not on
concern leaves. ``Chain`` is ``AllOf``.
"""

from __future__ import annotations

from typing import Any, Iterable

from ux_valio.descriptor import _annotations_agree
from ux_valio.validators.base import ValidateProperty
from ux_valio.validators.errors import ValidationErrors, continue_or_raise, raise_collected
from ux_valio.validators.hooks import HookHost, hook_bags_used
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


def _merged_attr(validators: tuple[Any, ...], attr: str, unspecified: Any) -> Any:
    present = [
        getattr(item, attr, unspecified)
        for item in validators
        if getattr(item, attr, unspecified) is not unspecified
    ]
    if not present:
        return unspecified
    first = present[0]
    for item in present[1:]:
        if item != first:
            raise TypeError(
                f"composed validators have conflicting {attr}: {first!r} vs {item!r}"
            )
    return first


def _keep_nested_compose(item: Any) -> bool:
    members = getattr(item, "validators", None)
    if not members:
        return False
    if hook_bags_used(item):
        return True
    for attr, unspecified in (
        ("debug", None),
        ("default", None),
        ("doc", None),
        ("logger", False),
        ("collect_all", False),
    ):
        merged = _merged_attr(members, attr, unspecified)
        if getattr(item, attr, unspecified) != merged:
            return True
    return False


def _flatten(cls: type, parts: Iterable[ValidateProperty]) -> tuple[ValidateProperty, ...]:
    out: list[ValidateProperty] = []
    for item in parts:
        if type(item) is cls and not _keep_nested_compose(item):
            out.extend(item.validators)  # type: ignore[attr-defined]
        else:
            out.append(item)
    return tuple(out)


def _bind_compose_kwargs(
    validators: tuple[ValidateProperty, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    kwargs.setdefault("debug", _merged_attr(validators, "debug", None))
    kwargs.setdefault("logger", _merged_attr(validators, "logger", False))
    kwargs.setdefault("default", _merged_attr(validators, "default", None))
    kwargs.setdefault("doc", _merged_attr(validators, "doc", None))
    kwargs.setdefault("collect_all", _merged_attr(validators, "collect_all", False))
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


class _Compose(HookHost, ValidateProperty):
    """Shared Door A descriptor for stacked validators. Owns root ``add_*`` bags."""

    validators: tuple[ValidateProperty, ...]

    def __init__(self, *validators: ValidateProperty, **kwargs: Any) -> None:
        self.validators = _flatten(type(self), _as_validators(validators))
        annotation = _compose_annotation(self.validators)
        if annotation is not None:
            self.annotation = annotation
        self._init_hook_bags()
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


class AllOf(_Compose):
    """AND composition: every member must validate. One Door A descriptor.

    ``Chain`` is this class. ``&`` and ``AllOf`` are the taught AND path.
    """

    def validate(self, instance: Any = None, value: Any = None) -> None:
        errors: list[BaseException] = []
        try:
            TypeValidator._validate_type(self, instance, value)
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        for item in self.validators:
            try:
                item.validate(instance=instance, value=value)
            except Exception as err:
                continue_or_raise(self.collect_all, errors, err)
        try:
            self._run_custom_validators(instance, value)
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        raise_collected(errors, name=self.name)


Chain = AllOf


class AnyOf(_Compose):
    """OR composition: the first member that validates wins."""

    def validate(self, instance: Any = None, value: Any = None) -> None:
        errors: list[BaseException] = []
        try:
            TypeValidator._validate_type(self, instance, value)
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        raise_collected(errors, name=self.name)
        alt_errors: list[BaseException] = []
        for item in self.validators:
            try:
                item.validate(instance=instance, value=value)
                break
            except Exception as err:
                if isinstance(err, ValidationErrors):
                    alt_errors.extend(err.errors)
                else:
                    alt_errors.append(err)
        else:
            if self.collect_all and alt_errors:
                raise_collected(alt_errors, name=self.name)
            label = self.name if self.name is not None else type(self).__name__
            raise ValueError(f"{label} matched none of the alternatives") from (
                alt_errors[-1] if alt_errors else None
            )
        try:
            self._run_custom_validators(instance, value)
        except Exception as err:
            continue_or_raise(self.collect_all, errors, err)
        raise_collected(errors, name=self.name)
