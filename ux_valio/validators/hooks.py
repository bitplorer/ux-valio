# SPDX-License-Identifier: MIT
"""Processor and task registries.

Hang ``add_process_*`` / ``add_task_*`` on the field default. Process
must finish. Task is background (email); persist/reserve that must
fail-closed hangs on ``add_process_post_set``. No ``add_pre_set``.
"""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Callable

from ux_valio.validators.async_bridge import invoke_callable, spawn_task, wait_tasks

from ux_valio.errors import continue_or_raise, raise_collected


class HookHost:
    """Processor and task registries on the validating descriptor.

    ``add_process_{phase}`` — transform; return is the pipeline value.
    Stored only for ``pre_validate`` / ``post_validate`` (inside ``pre_set``).
    ``add_task_{phase}`` — background side effect; return ignored; setter
    does not wait. Not the nest-safe pool. Hang persist/reserve that must
    fail-closed on ``add_process_post_set``. Hang email on
    ``add_task_post_set``. ``add_validator`` — check during ``validate()``.
    No ``add_process_pre_set`` — ``pre_set`` *is* the validate pipeline.
    """

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

    def _iter_owner_keys(self, instance: Any) -> tuple[str, ...]:
        """Owner keys for this run. ``_hook_schema`` is a TypedDict class.

        TypedDict values are dicts at runtime, so instance MRO is ``dict``.
        Hooks hung on the TypedDict (``@name.add_*`` in that class body) live
        under the schema's ``module.qualname``.
        """
        seen: set[str] = set()
        keys: list[str] = []
        schema = getattr(self, "_hook_schema", None)
        if schema is not None:
            for cls in getattr(schema, "__mro__", ()):
                if cls is object or cls is dict:
                    continue
                key = HookHost._owner_key(cls)
                if key in seen:
                    continue
                seen.add(key)
                keys.append(key)
            keys.reverse()
        if instance is not None:
            for key in HookHost._collect_owner_keys(instance):
                if key in seen:
                    continue
                seen.add(key)
                keys.append(key)
        return tuple(keys)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Phases are these dict keys. No add_pre_set — ValidateProperty.pre_set
        # *is* pre_validate → validate → post_validate.
        self._custom_validators: dict[str, list[Callable[..., Any]]] = defaultdict(list)
        self._processors: dict[str, dict[str, list[Callable[..., Any]]]] = {
            "pre_validate": defaultdict(list),
            "post_validate": defaultdict(list),
            "post_set": defaultdict(list),
            "pre_get": defaultdict(list),
            "post_get": defaultdict(list),
            "pre_delete": defaultdict(list),
            "post_delete": defaultdict(list),
        }
        self._tasks: dict[str, dict[str, list[Callable[..., Any]]]] = {
            phase: defaultdict(list) for phase in self._processors
        }
        super().__init__(*args, **kwargs)

    def _register(
        self,
        bucket: dict[str, list[Callable[..., Any]]],
        func: Callable[..., Any],
        namespace: str | None = None,
    ) -> Callable[..., Any]:
        key = HookHost._resolve_owner_key(
            func, namespace, getattr(self, "_owner", None)
        )
        bucket[key].append(func)
        return func

    def add_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Check during ``validate()``. Return ignored."""
        return self._register(self._custom_validators, func, namespace)

    def add_process_pre_validate(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform before validate. Return is stored (inside ``pre_set``)."""
        return self._register(self._processors["pre_validate"], func, namespace)

    def add_process_post_validate(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform after validate. Return is stored (inside ``pre_set``)."""
        return self._register(self._processors["post_validate"], func, namespace)

    def add_process_post_set(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform after store. Return is not stored."""
        return self._register(self._processors["post_set"], func, namespace)

    def add_process_pre_get(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform before read. Return is not the stored value."""
        return self._register(self._processors["pre_get"], func, namespace)

    def add_process_post_get(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform after read. Return is not the stored value."""
        return self._register(self._processors["post_get"], func, namespace)

    def add_process_pre_delete(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform before delete. Return is not stored."""
        return self._register(self._processors["pre_delete"], func, namespace)

    def add_process_post_delete(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Transform after delete. Return is not stored."""
        return self._register(self._processors["post_delete"], func, namespace)

    def add_task_pre_validate(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background side effect before validate. Return ignored. Setter does not wait."""
        return self._register(self._tasks["pre_validate"], func, namespace)

    def add_task_post_validate(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background side effect after validate. Return ignored. Setter does not wait."""
        return self._register(self._tasks["post_validate"], func, namespace)

    def add_task_post_set(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background after store (email). Return ignored. Setter does not wait.

        Persist/reserve that must fail-closed hangs on ``add_process_post_set``.
        """
        return self._register(self._tasks["post_set"], func, namespace)

    def add_task_pre_get(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background side effect before read. Return ignored. Setter does not wait."""
        return self._register(self._tasks["pre_get"], func, namespace)

    def add_task_post_get(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background side effect after read. Return ignored. Setter does not wait."""
        return self._register(self._tasks["post_get"], func, namespace)

    def add_task_pre_delete(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background side effect before delete. Return ignored. Setter does not wait."""
        return self._register(self._tasks["pre_delete"], func, namespace)

    def add_task_post_delete(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        """Background side effect after delete. Return ignored. Setter does not wait."""
        return self._register(self._tasks["post_delete"], func, namespace)

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        hooks = self._processors[phase]
        for key in self._iter_owner_keys(instance):
            for func in hooks.get(key, ()):
                value = invoke_callable(func, instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        hooks = self._tasks[phase]
        for key in self._iter_owner_keys(instance):
            for func in hooks.get(key, ()):
                spawn_task(self, func, instance, value)
        return value

    @staticmethod
    def wait_tasks(timeout: float | None = None) -> None:
        """Wait for background ``add_task_*`` work."""
        wait_tasks(timeout)

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
        if instance is None and getattr(self, "_hook_schema", None) is None:
            return
        errors: list[BaseException] = []
        collect_all = getattr(self, "collect_all", True)
        name = getattr(self, "name", None)
        for key in self._iter_owner_keys(instance):
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
