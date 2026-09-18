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
from ux_valio.errors import continue_or_raise, raise_collected



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


def _resolve_bag_key(
    func: Callable[..., Any],
    namespace: str | None,
    bound_owner: type | None = None,
) -> str:
    """Bag key for register. Default is ``_bag_key`` of the owning class.

    ``namespace=`` is the key as-is (str). A free function has no owning
    class: if the descriptor is already bound, use that owner; otherwise
    ``namespace=`` is required. Class objects are not keys.
    """
    if namespace is not None:
        if not isinstance(namespace, str):
            raise TypeError(
                "namespace= must be a str bag key "
                f"(module.qualname); got {type(namespace).__name__}"
            )
        return namespace
    owner = _owning_class_qualname(func)
    if owner is not None:
        return _bag_key(
            SimpleNamespace(__module__=func.__module__, __qualname__=owner)
        )
    if bound_owner is not None:
        return _bag_key(bound_owner)
    raise TypeError(
        "free function requires namespace= "
        "(bag key is module.qualname of the owning class)"
    )


def _hook_adder(bag: str, phase: str):
    """One body for every taught ``add_*``. Bound onto ``HookHost`` from its table."""

    def adder(
        self: "HookHost",
        func: Callable[..., Any],
        namespace: str | None = None,
    ) -> Callable[..., Any]:
        return self._add(bag, phase, func, namespace)

    return adder


class HookHost:
    """Processor/task/custom-validator bags. Mixin for facade and compose roots.

    Taught ``add_*`` names live on this class. Bodies are ``_add``. There is
    no ``add_pre_set`` / ``_processors["pre_set"]`` bag.
    """

    cache_task: bool  # leftover: stored, never consulted (cache retired)
    _custom_validators: dict[str, list[Callable[..., Any]]]
    _processors: dict[str, dict[str, list[Callable[..., Any]]]]
    _tasks: dict[str, dict[str, list[Callable[..., Any]]]]

    # No "pre_set": ValidateProperty.pre_set *is* pre_validate →
    # validate → post_validate. add_pre_set would be a second door.
    _PROCESSOR_PHASES = (
        "pre_validate",
        "post_validate",
        "post_set",
        "pre_get",
        "post_get",
        "pre_delete",
        "post_delete",
    )

    # Taught names. (method, bag, phase). Installed by ``_install_adders``.
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
    def _collect_bag_keys(instance: Any) -> tuple[str, ...]:
        """Owner keys from base to derived. Inherited hooks fire on a child."""
        keys: list[str] = []
        seen: set[str] = set()
        for cls in instance.__class__.__mro__:
            if cls is object:
                continue
            key = _bag_key(cls)
            if key in seen:
                continue
            seen.add(key)
            keys.append(key)
        keys.reverse()
        return tuple(keys)

    def _init_hook_bags(self, cache_task: bool = True) -> None:
        # valio leftover: keep the kwarg. Do not skip tasks from this flag.
        self.cache_task = cache_task
        self._custom_validators = defaultdict(list)
        self._processors = {
            phase: defaultdict(list) for phase in type(self)._PROCESSOR_PHASES
        }
        self._tasks = {phase: defaultdict(list) for phase in type(self)._PROCESSOR_PHASES}

    def _add(
        self,
        bag: str,
        phase: str,
        func: Callable[..., Any],
        namespace: str | None = None,
    ) -> Callable[..., Any]:
        getattr(self, bag)[phase][
            _resolve_bag_key(func, namespace, getattr(self, "_owner", None))
        ].append(func)
        return func

    def add_validator(self, func: Callable[..., Any], namespace: str | None = None) -> Callable[..., Any]:
        self._custom_validators[
            _resolve_bag_key(func, namespace, getattr(self, "_owner", None))
        ].append(func)
        return func

    def _run_processors(self, phase: str, instance: Any, value: Any) -> Any:
        bag = self._processors[phase]
        for key in type(self)._collect_bag_keys(instance):
            for func in bag.get(key, ()):
                value = invoke_callable(func, instance, value)
        return value

    def _run_tasks(self, phase: str, instance: Any, value: Any) -> Any:
        bag = self._tasks[phase]
        for key in type(self)._collect_bag_keys(instance):
            for func in bag.get(key, ()):
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
        for key in type(self)._collect_bag_keys(instance):
            for func in self._custom_validators.get(key, ()):
                try:
                    invoke_callable(func, instance, value)
                except Exception as err:
                    continue_or_raise(collect_all, errors, err)
        raise_collected(errors, name=name)

    @staticmethod
    def bags_used(item: Any) -> bool:
        """True when this host has a custom / processor / task bag with callables."""
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

    @classmethod
    def _install_adders(cls) -> None:
        """Taught add_* names. One encoding. No pre_set adder."""
        for name, bag, phase in cls._HOOK_ADDERS:
            adder = _hook_adder(bag, phase)
            adder.__name__ = name
            adder.__qualname__ = f"{cls.__name__}.{name}"
            setattr(cls, name, adder)


HookHost._install_adders()
