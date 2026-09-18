# SPDX-License-Identifier: MIT
"""Validator↔validator composition: AllOf / AnyOf as one Door A descriptor.

Facades do not multiple-inherit concern leaves. ``&`` / ``|`` stacks validator
*objects* into one descriptor. Hang ``add_*`` on this compose *root*, not on
concern leaves. ``Chain`` is ``AllOf``.
"""

from __future__ import annotations

from typing import Any, Iterable

from ux_valio.descriptor import _Opt, _annotations_agree
from ux_valio.errors import ValidationErrors, raise_collected, run_steps
from ux_valio.validators.base import ValidateProperty, _register_compose_types

from ux_valio.validators.hooks import HookHost
from ux_valio.validators.leaves import TypeValidator


class _Compose(HookHost, ValidateProperty):
    """AllOf / AnyOf share flatten, specified-theory merge, and member process order."""

    validators: tuple[ValidateProperty, ...]
    _merge_member_annotations = True
    _propagate_annotation = True

    def __init__(self, *validators: ValidateProperty, cache_task: bool = True, **kwargs: Any) -> None:
        self.validators = type(self)._flatten(type(self)._as_validators(validators))
        if type(self)._merge_member_annotations:
            annotation = type(self)._merged_annotation(self.validators)
            if annotation is not None:
                self.annotation = annotation
        self._init_hook_bags(cache_task=cache_task)
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
        members = getattr(item, "validators", None)
        if not members:
            return False
        if HookHost.bags_used(item):
            return True
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
        kwargs.setdefault("debug", _Compose._merged_attr(validators, "debug", None))
        kwargs.setdefault("default", _Compose._merged_attr(validators, "default", None))
        kwargs.setdefault(
            "default_factory", _Compose._merged_attr(validators, "default_factory", None)
        )
        kwargs.setdefault("doc", _Compose._merged_attr(validators, "doc", None))
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

    def _compose_process(self, phase: str, method: str, instance: Any, value: Any) -> Any:
        if phase.startswith("pre_"):
            value = self._process_then_tasks(phase, instance, value)
            for item in self.validators:
                value = getattr(item, method)(instance, value)
            return value
        for item in self.validators:
            value = getattr(item, method)(instance, value)
        return self._process_then_tasks(phase, instance, value)

    def pre_validation_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("pre_validate", "pre_validation_processing", instance, value)

    def post_validation_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("post_validate", "post_validation_processing", instance, value)

    def post_set_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("post_set", "post_set_processing", instance, value)

    def pre_get_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("pre_get", "pre_get_processing", instance, value)

    def post_get_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("post_get", "post_get_processing", instance, value)

    def pre_delete_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("pre_delete", "pre_delete_processing", instance, value)

    def post_delete_processing(self, instance: Any, value: Any) -> Any:
        return self._compose_process("post_delete", "post_delete_processing", instance, value)


class AllOf(_Compose):
    def validate(self, instance: Any = None, value: Any = None) -> None:
        run_steps(
            (
                lambda: TypeValidator._validate_type(self, instance, value),
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


class AnyOf(_Compose):
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

        ``instance is None`` skips member custom bags. Path bounds on
        members are the alternatives.
        """
        super()._reject_store_identity(value)
        self._match_one_alternative(None, value)


_register_compose_types(AllOf, AnyOf)
