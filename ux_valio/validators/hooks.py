# SPDX-License-Identifier: MIT
"""Processor and task registries for Validator and compose roots.

Hang ``add_*`` on the descriptor that is the field default. There is no
``add_pre_set`` / ``_processors["pre_set"]`` registry.
"""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Callable

from ux_valio.validators.async_bridge import invoke_callable
from ux_valio.errors import continue_or_raise, raise_collected


class HookHost:
    """Processor, task, and custom-validator registries on the facade / compose root.

    Public ``add_*`` methods live here; bodies call ``_add``. There is no
    ``add_pre_set`` registry. Register and lookup share one owner key:
    ``module.qualname`` of the class that owns the hook.
    """

    _custom_validators: dict[str, list[Callable[..., Any]]]
    _processors: dict[str, dict[str, list[Callable[..., Any]]]]
    _tasks: dict[str, dict[str, list[Callable[..., Any]]]]

    # No "pre_set": ValidateProperty.pre_set *is* pre_validate →
    # validate → post_validate. add_pre_set would be a second assignment path.
    _PROCESSOR_PHASES = (
        "pre_validate",
        "post_validate",
        "post_set",
        "pre_get",
        "post_get",
        "pre_delete",
        "post_delete",
    )

    # Public add_* methods. (method, registry attribute, phase).
    _HOOK_ADDERS = (
        ("add_pre_validator", "_processors", "pre_validate"),
        ("add_post_validator", "_processors", "post_validate"),
        ("add_post_set", "_processors", "post_set"),
        ("add_pre_get", "_processors", "pre_get"),
        ("add_post_get", "_processors", "post_get"),
        ("add_pre_delete", "_processors", "pre_delete"),
        ("add_post_delete", "_processors", "post_delete"),
        ("add_pre_validator_task", "_tasks", "pre_validate"),
        ("add_post_validator_task", "_tasks", "post_validate"),
        ("add_post_set_task", "_tasks", "post_set"),
        ("add_pre_get_task", "_tasks", "pre_get"),
        ("add_post_get_task", "_tasks", "post_get"),
        ("add_pre_delete_task", "_tasks", "pre_delete"),
        ("add_post_delete_task", "_tasks", "post_delete"),
    )

    @staticmethod
    def _owner_key(cls: Any) -> str:
        """Owning class identity for register and lookup: ``module.qualname``."""
        return f"{cls.__module__}.{cls.__qualname__}"

    @staticmethod
    def _owning_class_qualname(func: Callable[..., Any]) -> str | None:
        """Owning-class qualname, or None for a free function."""
        qualname = str(getattr(func, "__qualname__", "") or "")
        if "." not in qualname:
            return None
        owner = qualname.rsplit(".", 1)[0]
        if owner.endswith(".<locals>") or owner in {"<locals>", ""}:
            return None
        return owner

    @staticmethod
    def _resolve_owner_key(
        func: Callable[..., Any],
        namespace: str | None,
        bound_owner: type | None = None,
    ) -> str:
        """Owner key used when registering a hook.

        Default is ``_owner_key`` of the function's owning class.
        ``namespace=`` is that key as-is (str). A free function has no
        owning class: if the descriptor is already bound, use that owner;
        otherwise ``namespace=`` is required. Class objects are not keys.
        """
        if namespace is not None:
            if not isinstance(namespace, str):
                raise TypeError(
                    "namespace= must be a str owner key "
                    f"(module.qualname); got {type(namespace).__name__}"
                )
            return namespace
        owner = HookHost._owning_class_qualname(func)
        if owner is not None:
            return HookHost._owner_key(
                SimpleNamespace(__module__=func.__module__, __qualname__=owner)
            )
        if bound_owner is not None:
            return HookHost._owner_key(bound_owner)
        raise TypeError(
            "free function requires namespace= "
            "(owner key is module.qualname of the owning class)"
        )

    @staticmethod
    def _hook_adder(registry: str, phase: str):
        """One body for every public ``add_*``. Bound onto ``HookHost`` from its table."""

        def adder(
            self: "HookHost",
            func: Callable[..., Any],
            namespace: str | None = None,
        ) -> Callable[..., Any]:
            return self._add(registry, phase, func, namespace)

        return adder

    @staticmethod
    def _collect_owner_keys(instance: Any) -> tuple[str, ...]:
        """Owner keys from base to derived. Inherited hooks fire on a child."""
        keys: list[str] = []
        seen: set[str] = set()
        for cls in instance.__class__.__mro__:
            if cls is object:
                continue
            key = HookHost._owner_key(cls)
            if key in seen:
                continue
            seen.add(key)
            keys.append(key)
        keys.reverse()
        return tuple(keys)

    def _init_hooks(self) -> None:
        self._custom_validators = defaultdict(list)
        self._processors = {
            phase: defaultdict(list) for phase in type(self)._PROCESSOR_PHASES
        }
        self._tasks = {phase: defaultdict(list) for phase in type(self)._PROCESSOR_PHASES}

    def _add(
        self,
        registry: str,
        phase: str,
        func: Callable[..., Any],
        namespace: str | None = None,
    ) -> Callable[..., Any]:
        getattr(self, registry)[phase][
            HookHost._resolve_owner_key(func, namespace, getattr(self, "_owner", None))
        ].append(func)
        return func

    def add_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._custom_validators[
            HookHost._resolve_owner_key(func, namespace, getattr(self, "_owner", None))
        ].append(func)
        return func

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        hooks = self._processors[phase]
        for key in type(self)._collect_owner_keys(instance):
            for func in hooks.get(key, ()):
                value = invoke_callable(func, instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        hooks = self._tasks[phase]
        for key in type(self)._collect_owner_keys(instance):
            for func in hooks.get(key, ()):
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
        for key in type(self)._collect_owner_keys(instance):
            for func in self._custom_validators.get(key, ()):
                try:
                    invoke_callable(func, instance, value)
                except Exception as err:
                    continue_or_raise(collect_all, errors, err)
        raise_collected(errors, name=name)

    @staticmethod
    def has_hooks(item: Any) -> bool:
        """True when this host has a custom, processor, or task callable registered."""
        customs = getattr(item, "_custom_validators", None)
        if customs and any(customs.values()):
            return True
        for registry_name in ("_processors", "_tasks"):
            registries = getattr(item, registry_name, None)
            if not registries:
                continue
            for phase in registries.values():
                if any(phase.values()):
                    return True
        return False

    @classmethod
    def _install_adders(cls) -> None:
        """Public add_* names. One encoding. No pre_set adder."""
        for name, registry, phase in cls._HOOK_ADDERS:
            adder = cls._hook_adder(registry, phase)
            adder.__name__ = name
            adder.__qualname__ = f"{cls.__name__}.{name}"
            setattr(cls, name, adder)


HookHost._install_adders()
