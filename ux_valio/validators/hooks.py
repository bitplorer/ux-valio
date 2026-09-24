# SPDX-License-Identifier: MIT
"""Processor and task registries.

Hang ``pre_validate`` / ``validator`` / ``post_set`` / ``task_*`` on the field default. Process
must finish. Task is background (email); persist/reserve that must
fail-closed hangs on ``post_set``. No ``add_pre_set``.
"""

from __future__ import annotations

import weakref
from collections import defaultdict
from types import SimpleNamespace
from typing import Any, Callable, NamedTuple, is_typeddict

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
# Set phases are compiled. Get/delete stay on the open owner-key walk.
_SET_PHASES = frozenset({"pre_validate", "post_validate", "post_set"})


class _ClosedHangs(NamedTuple):
    """MRO-flattened set-phase callables for one owning class.

    Processors and ``task_*`` are separate tuples so a phase with no
    background work does not spawn. This is a cache row, not a field-wide
    ``_closed_set``.
    """

    pre_validate: tuple[Callable[..., Any], ...]
    task_pre_validate: tuple[Callable[..., Any], ...]
    post_validate: tuple[Callable[..., Any], ...]
    task_post_validate: tuple[Callable[..., Any], ...]
    post_set: tuple[Callable[..., Any], ...]
    task_post_set: tuple[Callable[..., Any], ...]
    validator: tuple[Callable[..., Any], ...]


_TRACKED_FIELDS: weakref.WeakKeyDictionary[type, list[weakref.ref[Any]]] = (
    weakref.WeakKeyDictionary()
)
_ARMED_OWNERS: weakref.WeakSet[type] = weakref.WeakSet()


def _push_owner(owner: Any, pending: list[type], seen: set[type]) -> None:
    if not isinstance(owner, type) or owner is object or owner in seen:
        return
    seen.add(owner)
    pending.append(owner)
    for sub in owner.__subclasses__():
        _push_owner(sub, pending, seen)


def _recompile_tracked_fields(cls: type) -> None:
    """Bake inherited fields for a class created after the last register."""
    seen: set[int] = set()
    for base in cls.__mro__:
        refs = _TRACKED_FIELDS.get(base)
        if not refs:
            continue
        live: list[weakref.ref[Any]] = []
        for ref in refs:
            field = ref()
            if field is None:
                continue
            live.append(ref)
            ident = id(field)
            if ident in seen:
                continue
            seen.add(ident)
            field._recompile_tree((cls,))
        _TRACKED_FIELDS[base] = live


def _arm_owner_recompile(owner: type) -> None:
    """Future subclasses get a closed list before any assignment."""
    if owner in _ARMED_OWNERS:
        return
    _ARMED_OWNERS.add(owner)
    prior = owner.__dict__.get("__init_subclass__")

    def _recompile_subclasses(cls: type, **kwargs: Any) -> None:
        if prior is None:
            super(owner, cls).__init_subclass__(**kwargs)  # type: ignore[arg-type]
        else:
            func = prior.__func__ if isinstance(prior, classmethod) else prior
            func(cls, **kwargs)
        _recompile_tracked_fields(cls)

    setattr(owner, "__init_subclass__", classmethod(_recompile_subclasses))


def _track_field_owner(owner: type, field: Any) -> None:
    refs = _TRACKED_FIELDS.get(owner)
    if refs is None:
        refs = []
        _TRACKED_FIELDS[owner] = refs
    for ref in refs:
        if ref() is field:
            _arm_owner_recompile(owner)
            return
    refs.append(weakref.ref(field))
    _arm_owner_recompile(owner)


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
    def _read_owner_keys(cls: type) -> tuple[str, ...]:
        """Owner keys from base to derived for one class's MRO."""
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

    @staticmethod
    def _collect_owner_keys(instance: Any, bound: type | None = None) -> tuple[str, ...]:
        """Owner keys from base to derived. Inherited hooks fire on a child.

        TypedDict values are dicts, so instance MRO is ``dict``. When
        ``__set_name__`` bound this descriptor to a TypedDict, look up
        that class (the class body that hung ``@name.pre_validate``).
        Get/delete still use this. Set phases use ``_closed`` instead.
        """
        cls = bound if bound is not None and is_typeddict(bound) else None
        if cls is None:
            if instance is None:
                return ()
            cls = instance.__class__
        return HookHost._read_owner_keys(cls)

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
        # Per owning class. Not one field-wide ``_closed_set``.
        self._closed: dict[type, _ClosedHangs] = {}
        self._closed_uses_owner = False
        super().__init__(*args, **kwargs)

    def _warm_closed(self, owner: type) -> None:
        _track_field_owner(owner, self)
        self._recompile_tree((owner,))

    def _recompile_tree(self, affected_owners: tuple[type, ...] | list[type]) -> None:
        """Recompile this field and nested ``_Of`` members for ``affected_owners``."""
        self._recompile_closed(affected_owners)
        children = getattr(self, "validators", None)
        if not children:
            return
        for item in children:
            recompile = getattr(item, "_recompile_tree", None)
            if recompile is not None:
                recompile(affected_owners)

    def _affected_owners(self, key: str, hinted: type | None) -> tuple[type, ...]:
        found: list[type] = []
        seen: set[type] = set()
        if hinted is not None:
            found.append(hinted)
            seen.add(hinted)
        for cls in tuple(self._closed):
            if cls in seen:
                continue
            for item in cls.__mro__:
                if item is object:
                    continue
                if HookHost._owner_key(item) == key:
                    found.append(cls)
                    seen.add(cls)
                    break
        return tuple(found)

    def _compile_closed(self, owner: type) -> _ClosedHangs:
        """Flatten open buckets across ``owner``'s MRO. Does not replace them."""
        keys = HookHost._read_owner_keys(owner)

        def take(bucket: dict[str, list[Callable[..., Any]]]) -> tuple[Callable[..., Any], ...]:
            out: list[Callable[..., Any]] = []
            for owner_key in keys:
                found = bucket.get(owner_key)
                if found:
                    out.extend(found)
            return tuple(out)

        processors = self._processors
        tasks = self._tasks
        return _ClosedHangs(
            pre_validate=take(processors["pre_validate"]),
            task_pre_validate=take(tasks["pre_validate"]),
            post_validate=take(processors["post_validate"]),
            task_post_validate=take(tasks["post_validate"]),
            post_set=take(processors["post_set"]),
            task_post_set=take(tasks["post_set"]),
            validator=take(self._custom_validators),
        )

    def _recompile_closed(self, affected_owners: tuple[type, ...] | list[type]) -> None:
        """WRITE path. Rebuild ``_closed`` for these owners and known subclasses."""
        pending: list[type] = []
        seen: set[type] = set()
        for owner in affected_owners:
            _push_owner(owner, pending, seen)
        for owner in pending:
            self._closed[owner] = self._compile_closed(owner)

    def _require_closed(self, instance: Any) -> _ClosedHangs | None:
        """READ path. Missing owner is fail-closed. ``None`` instance skips.

        No set-phase hang does not call this: that set stays the #135 door.
        The common key is ``type(instance)``. A TypedDict owner is the
        bound class, because the mapping's type is ``dict``.
        """
        bound = getattr(self, "_owner", None)
        if self._closed_uses_owner and isinstance(bound, type) and is_typeddict(bound):
            key: type = bound
        elif instance is None:
            return None
        else:
            key = type(instance)
        closed = self._closed.get(key)
        if closed is None:
            raise TypeError(
                f"{key.__qualname__}.{getattr(self, 'name', None)}: "
                "hang list is not compiled for this class"
            )
        return closed

    def _register(
        self,
        bucket: dict[str, list[Callable[..., Any]]],
        func: Callable[..., Any],
        namespace: type | str | None = None,
        phase_bit: int = 0,
    ) -> Callable[..., Any]:
        bound = getattr(self, "_owner", None)
        key = HookHost._resolve_owner_key(
            func, namespace, bound if isinstance(bound, type) else None
        )
        bucket[key].append(func)
        self._phase_mask |= phase_bit
        self._hooks_hung = True
        hinted = namespace if isinstance(namespace, type) else None
        if (
            hinted is None
            and isinstance(bound, type)
            and HookHost._owner_key(bound) == key
        ):
            hinted = bound
        self._recompile_closed(self._affected_owners(key, hinted))
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

    def _run_closed_processors(
        self, funcs: tuple[Callable[..., Any], ...], instance: Any, value: Any
    ) -> Any:
        for func in funcs:
            value = invoke_callable(func, instance, value)
        return value

    def _spawn_closed_tasks(
        self, funcs: tuple[Callable[..., Any], ...], instance: Any, value: Any
    ) -> None:
        for func in funcs:
            spawn_task(self, func, instance, value)

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        if phase in _SET_PHASES:
            closed = self._require_closed(instance)
            if closed is None:
                return value
            return self._run_closed_processors(getattr(closed, phase), instance, value)
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
        if phase in _SET_PHASES:
            closed = self._require_closed(instance)
            if closed is None:
                return value
            funcs = getattr(closed, f"task_{phase}")
            if funcs:
                self._spawn_closed_tasks(funcs, instance, value)
            return value
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

    def _run_sealed_phase(self, closed: _ClosedHangs, phase: str, instance: Any, value: Any) -> Any:
        if phase == "pre_validate":
            procs = closed.pre_validate
            tasks = closed.task_pre_validate
        elif phase == "post_validate":
            procs = closed.post_validate
            tasks = closed.task_post_validate
        else:
            procs = closed.post_set
            tasks = closed.task_post_set
        if procs:
            value = self._run_closed_processors(procs, instance, value)
        if tasks:
            self._spawn_closed_tasks(tasks, instance, value)
        return value

    def _process_then_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        # Empty phase: no owner-key walk. A get/delete hang does not
        # make set walk ``pre_validate`` / ``post_validate`` / ``post_set``.
        if (self._phase_mask & _PHASE_BITS[phase]) == 0:
            return value
        if phase in _SET_PHASES:
            closed = self._require_closed(instance)
            if closed is None:
                return value
            return self._run_sealed_phase(closed, phase, instance, value)
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
        if (self._phase_mask & _PHASE_VALIDATOR) == 0:
            return
        closed = self._require_closed(instance)
        if closed is None or not closed.validator:
            return
        errors: list[BaseException] = []
        collect_all = getattr(self, "collect_all", True)
        name = getattr(self, "name", None)
        for func in closed.validator:
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
