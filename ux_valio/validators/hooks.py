# SPDX-License-Identifier: MIT
"""Processor and task registries.

Hang ``pre_validate`` / ``validator`` / ``post_set`` / ``task_*`` on the field default. Process
must finish. Task is background (email); persist/reserve that must
fail-closed hangs on ``post_set``. No ``add_pre_set``.
"""

from __future__ import annotations

from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Callable, is_typeddict

from ux_valio.validators.async_bridge import (
    invoke_callable,
    spawn_task,
    wait_tasks as wait_tasks_impl,
)


from ux_valio.errors import continue_or_raise, raise_collected


# One bit per hang phase. Set phases are the ones ``__set__`` must not skip.
_PHASE_PRE_VALIDATE = 1
_PHASE_POST_VALIDATE = 2
_PHASE_POST_SET = 4
_PHASE_PRE_GET = 8
_PHASE_POST_GET = 16
_PHASE_PRE_DELETE = 32
_PHASE_POST_DELETE = 64
_PHASE_VALIDATOR = 128
_SET_PHASE_MASK = (
    _PHASE_PRE_VALIDATE | _PHASE_POST_VALIDATE | _PHASE_POST_SET | _PHASE_VALIDATOR
)
_PHASE_BITS = {
    "pre_validate": _PHASE_PRE_VALIDATE,
    "post_validate": _PHASE_POST_VALIDATE,
    "post_set": _PHASE_POST_SET,
    "pre_get": _PHASE_PRE_GET,
    "post_get": _PHASE_POST_GET,
    "pre_delete": _PHASE_PRE_DELETE,
    "post_delete": _PHASE_POST_DELETE,
}


class HookHost:
    """Processor and task registries on the validating descriptor.

    Public hang API: ``pre_validate`` / ``post_set`` / … (process; return
    is the pipeline value), ``task_{phase}`` (background), ``validator``,
    ``wait_tasks``. Process is the default kind — no ``process_`` prefix.
    ``post_set`` is hang, not the descriptor lifecycle (that is
    ``_run_post_set``). No hang named ``pre_set`` — ``_run_pre_set`` *is*
    ``pre_validate → validate → post_validate``. ``validator`` is the check
    (attrs ``@x.validator``); ``validate()`` runs it. Pipeline runners
    (``_pre_validate``, …) are private.
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
        namespace: type | str | None,

        bound_owner: type | None = None,
    ) -> str:
        """Owner key used when registering a hook.

        Default is ``_owner_key`` of the function's owning class.
        ``namespace=`` is that class, or its ``module.qualname`` str.
        A free function has no owning class: if the descriptor is already
        bound, use that owner; otherwise ``namespace=`` is required.
        """
        if namespace is not None:
            if isinstance(namespace, type):
                return HookHost._owner_key(namespace)
            if not isinstance(namespace, str):
                raise TypeError(
                    "namespace= must be the owning class or its "
                    f"module.qualname str; got {type(namespace).__name__}"
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
    def _collect_owner_keys(instance: Any, bound: type | None = None) -> tuple[str, ...]:
        """Owner keys from base to derived. Inherited hooks fire on a child.

        TypedDict values are dicts, so instance MRO is ``dict``. When
        ``__set_name__`` bound this descriptor to a TypedDict, look up
        that class (the class body that hung ``@name.pre_validate``).
        """
        cls = bound if bound is not None and is_typeddict(bound) else None
        if cls is None:
            if instance is None:
                return ()
            cls = instance.__class__
        keys: list[str] = []
        seen: set[str] = set()
        for item in cls.__mro__:
            if item is object:
                continue
            key = HookHost._owner_key(item)
            if key in seen:
                continue
            seen.add(key)
            keys.append(key)
        keys.reverse()
        return tuple(keys)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Phases are these dict keys. No hang pre_set — ValidateProperty._run_pre_set
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
        self._phase_mask = 0
        self._hooks_hung = False
        super().__init__(*args, **kwargs)

    def _register(
        self,
        bucket: dict[str, list[Callable[..., Any]]],
        func: Callable[..., Any],
        namespace: type | str | None = None,
        phase_bit: int = 0,
    ) -> Callable[..., Any]:
        key = HookHost._resolve_owner_key(
            func, namespace, getattr(self, "_owner", None)
        )
        bucket[key].append(func)
        self._phase_mask |= phase_bit
        self._hooks_hung = True
        return func

    def validator(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Check during ``validate()``. Return ignored."""
        return self._register(
            self._custom_validators, func, namespace, _PHASE_VALIDATOR
        )

    def pre_validate(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform before validate. Return is stored (inside ``_run_pre_set``)."""
        return self._register(
            self._processors["pre_validate"], func, namespace, _PHASE_PRE_VALIDATE
        )

    def post_validate(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform after validate. Return is stored (inside ``_run_pre_set``)."""
        return self._register(
            self._processors["post_validate"], func, namespace, _PHASE_POST_VALIDATE
        )

    def post_set(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform after store. Return is not stored."""
        return self._register(
            self._processors["post_set"], func, namespace, _PHASE_POST_SET
        )

    def pre_get(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform before read. Return is not the stored value."""
        return self._register(
            self._processors["pre_get"], func, namespace, _PHASE_PRE_GET
        )

    def post_get(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform after read. Return is not the stored value."""
        return self._register(
            self._processors["post_get"], func, namespace, _PHASE_POST_GET
        )

    def pre_delete(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform before delete. Return is not stored."""
        return self._register(
            self._processors["pre_delete"], func, namespace, _PHASE_PRE_DELETE
        )

    def post_delete(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Transform after delete. Return is not stored."""
        return self._register(
            self._processors["post_delete"], func, namespace, _PHASE_POST_DELETE
        )

    def task_pre_validate(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background side effect before validate. Return ignored. Setter does not wait."""
        return self._register(
            self._tasks["pre_validate"], func, namespace, _PHASE_PRE_VALIDATE
        )

    def task_post_validate(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background side effect after validate. Return ignored. Setter does not wait."""
        return self._register(
            self._tasks["post_validate"], func, namespace, _PHASE_POST_VALIDATE
        )

    def task_post_set(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background after store (email). Return ignored. Setter does not wait.

        Persist/reserve that must fail-closed hangs on ``post_set``.
        """
        return self._register(
            self._tasks["post_set"], func, namespace, _PHASE_POST_SET
        )

    def task_pre_get(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background side effect before read. Return ignored. Setter does not wait."""
        return self._register(self._tasks["pre_get"], func, namespace, _PHASE_PRE_GET)

    def task_post_get(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background side effect after read. Return ignored. Setter does not wait."""
        return self._register(
            self._tasks["post_get"], func, namespace, _PHASE_POST_GET
        )

    def task_pre_delete(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background side effect before delete. Return ignored. Setter does not wait."""
        return self._register(
            self._tasks["pre_delete"], func, namespace, _PHASE_PRE_DELETE
        )

    def task_post_delete(self, func: Callable[..., Any], namespace: type | str | None = None) -> Callable[..., Any]:
        """Background side effect after delete. Return ignored. Setter does not wait."""
        return self._register(
            self._tasks["post_delete"], func, namespace, _PHASE_POST_DELETE
        )

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        hooks = self._processors[phase]
        if not hooks:
            return value
        for key in HookHost._collect_owner_keys(
            instance, getattr(self, "_owner", None)
        ):
            for func in hooks.get(key, ()):
                value = invoke_callable(func, instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        hooks = self._tasks[phase]
        if not hooks:
            return value
        for key in HookHost._collect_owner_keys(
            instance, getattr(self, "_owner", None)
        ):
            for func in hooks.get(key, ()):
                spawn_task(self, func, instance, value)
        return value

    @staticmethod
    def wait_tasks(timeout: float | None = None) -> None:
        """Wait for background ``task_*`` work."""
        wait_tasks_impl(timeout)

    def _process_then_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        # Empty phase: no owner-key walk. A get/delete hang does not
        # make set walk ``pre_validate`` / ``post_validate`` / ``post_set``.
        if (self._phase_mask & _PHASE_BITS[phase]) == 0:
            return value
        value = self._run_processors(phase, instance, value)
        self._run_tasks(phase, instance, value)
        return value

    def _pre_validate(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("pre_validate", instance, value)

    def _post_validate(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_validate", instance, value)

    def _post_set(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_set", instance, value)

    def _pre_get(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("pre_get", instance, value)

    def _post_get(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_get", instance, value)

    def _pre_delete(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("pre_delete", instance, value)

    def _post_delete(self, instance: Any, value: Any) -> Any:
        return self._process_then_tasks("post_delete", instance, value)

    def _run_custom_validators(self, instance: Any, value: Any) -> None:
        if not self._custom_validators:
            return
        bound = getattr(self, "_owner", None)
        if instance is None and bound is None:
            return
        errors: list[BaseException] = []
        collect_all = getattr(self, "collect_all", True)
        name = getattr(self, "name", None)
        for key in HookHost._collect_owner_keys(instance, bound):
            for func in self._custom_validators.get(key, ()):
                try:
                    invoke_callable(func, instance, value)
                except Exception as err:
                    continue_or_raise(collect_all, errors, err)
        raise_collected(errors, name=name)

    @staticmethod
    def _has_hooks(item: Any) -> bool:
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
