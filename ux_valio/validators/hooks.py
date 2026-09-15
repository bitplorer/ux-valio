# SPDX-License-Identifier: MIT
"""Processor/task bags for Validator and compose roots — not concern leaves.

Hang ``add_*`` on the descriptor that is the field default. There is no
``add_pre_set`` / ``_processors["pre_set"]`` bag.
"""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Callable

from ux_valio.validators.async_bridge import invoke_callable
from ux_valio.validators.errors import continue_or_raise, raise_collected

_PROCESSOR_PHASES = (
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


def _bag_key(cls: Any) -> str:
    """One bag key for register and lookup: ``module.qualname``."""
    return f"{cls.__module__}.{cls.__qualname__}"


def _owning_class_qualname(func: Callable[..., Any]) -> str | None:
    """Owning-class qualname, or None for a free function."""
    qualname = str(getattr(func, "__qualname__", "") or "")
    if "." not in qualname:
        return None
    owner = qualname.rsplit(".", 1)[0]
    if owner.endswith(".<locals>") or owner in {"<locals>", ""}:
        return None
    return owner


def _namespace(func: Callable[..., Any], namespace: str | None) -> str:
    """Bag key. Default is ``_bag_key`` of the owning class.

    ``namespace=`` is the key as-is (str). A free function has no owning
    class and requires ``namespace=``. Class objects are not keys.
    """
    if namespace is not None:
        if not isinstance(namespace, str):
            raise TypeError(
                "namespace= must be a str bag key "
                f"(module.qualname); got {type(namespace).__name__}"
            )
        return namespace
    owner = _owning_class_qualname(func)
    if owner is None:
        raise TypeError(
            "free function requires namespace= "
            "(bag key is module.qualname of the owning class)"
        )
    return _bag_key(
        SimpleNamespace(__module__=func.__module__, __qualname__=owner)
    )


def hook_bags_used(item: Any) -> bool:
    customs = getattr(item, "_custom_validators", None)
    if customs and any(customs.values()):
        return True
    for bag_name in ("_processors", "_tasks"):
        bags = getattr(item, bag_name, None)
        if not bags:
            continue
        for phase in bags.values():
            if any(phase.values()):
                return True
    return False


class HookHost:
    """Processor/task/custom-validator bags. Mixin for facade and compose roots."""

    cache_task: bool
    _custom_validators: dict[str, list[Callable[..., Any]]]
    _processors: dict[str, dict[str, list[Callable[..., Any]]]]
    _tasks: dict[str, dict[str, list[Callable[..., Any]]]]

    def _init_hook_bags(self, cache_task: bool = True) -> None:
        self.cache_task = cache_task
        self._custom_validators = defaultdict(list)
        self._processors = {phase: defaultdict(list) for phase in _PROCESSOR_PHASES}
        self._tasks = {phase: defaultdict(list) for phase in _PROCESSOR_PHASES}

    def add_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._custom_validators[_namespace(func, namespace)].append(func)
        return func

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        for func in self._processors[phase].get(_bag_key(instance.__class__), ()):
            value = invoke_callable(func, instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        for func in self._tasks[phase].get(_bag_key(instance.__class__), ()):
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

    def _run_custom_validators(self, instance: Any, value: Any) -> None:
        if instance is None:
            return
        errors: list[BaseException] = []
        collect_all = getattr(self, "collect_all", False)
        name = getattr(self, "name", None)
        for func in self._custom_validators.get(_bag_key(instance.__class__), ()):
            try:
                invoke_callable(func, instance, value)
            except Exception as err:
                continue_or_raise(collect_all, errors, err)
        raise_collected(errors, name=name)

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
