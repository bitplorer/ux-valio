# SPDX-License-Identifier: MIT
"""Descriptor lifecycle.

``__set__`` applies ``default`` only when the assigned value ``is None``.
Falsy assigned values ``0`` / ``False`` / ``""`` are kept.

``debug`` falsy swallows exceptions, appends them to ``errors``, and does
not re-raise. ``debug=True`` re-raises. This swallow is KEEP — not a
silent fail-closed flip. ``collect_all`` (default ``False``) is a separate
opt-in: fail-fast remains the door. ``collect_all=True`` continues remaining
concerns and surfaces every failure. Do not overload ``debug`` into collect.

Class access (``obj is None``) returns ``None`` so dataclasses treat the
descriptor as a missing field default and route ``Cls()`` through
``__set__(instance, None)``, which then applies ``default``.

Only the descriptor ``pre_set`` hook return is stored. That hook is the
validate pipeline, not a ``_processors["pre_set"]`` bag. Hang before-store
work on ``add_pre_validator`` / ``add_validator`` / ``add_pre_validator_task``.
``post_set`` / get / delete return values are ignored. ``__get__`` /
``__delete__`` pass ``self.name`` into hooks, not the stored value.
``add_*`` may be async. No ``asyncio.run`` in ``__set__``.

Logger default is OFF.

``__set_name__`` is fail-closed on annotation conflict. If both
``validator.annotation`` and the owner class annotation are set and they
disagree, raise ``TypeError``. Owner wins only when the validator annotation
was ``None``. The validator annotation is kept when the owner has none.
Union forms and list/dict/tuple/set/frozenset aliases are compared with
stdlib ``get_origin`` / ``get_args`` (``typing.Union`` and ``X | Y``;
``list[T]`` and ``typing.List[T]``), not typingx / typing_extensions.
"""

from __future__ import annotations

import types
from typing import Any, Union, get_args, get_origin


_CONTAINER_ORIGINS = (list, dict, tuple, set, frozenset)


def _annotation_identity(annotation: Any) -> Any:
    """Hashable identity for stdlib union and container alias forms.

    ``Union[X, Y]`` and ``X | Y`` agree. ``list[T]`` and ``typing.List[T]``
    agree. Bare ``list`` is not ``list[int]``.
    """
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        return (Union, frozenset(_annotation_identity(arg) for arg in get_args(annotation)))
    if origin in _CONTAINER_ORIGINS:
        return (origin, tuple(_annotation_identity(arg) for arg in get_args(annotation)))
    if annotation in _CONTAINER_ORIGINS:
        return (annotation, ())
    return annotation


def _annotations_agree(left: Any, right: Any) -> bool:
    if left is right:
        return True
    return _annotation_identity(left) == _annotation_identity(right)


def _annotation_label(annotation: Any) -> str:
    if isinstance(annotation, str):
        return repr(annotation)
    return annotation.__name__ if hasattr(annotation, "__name__") else str(annotation)


class Property:
    """Data descriptor used as a dataclass field default (Door A)."""

    def __init__(
        self,
        name: str | None = None,
        default: Any = None,
        doc: str | None = None,
        debug: bool | None = None,
        logger: Any = False,
        collect_all: bool = False,
    ) -> None:
        if name is not None and not isinstance(name, str):
            raise TypeError(
                f"name expected type str value, got {type(name).__name__} type instead"
            )
        if doc is not None and not isinstance(doc, str):
            raise TypeError(
                f"doc expected type str value, got {type(doc).__name__} type instead"
            )
        if debug is not None and not isinstance(debug, bool):
            raise TypeError(
                f"debug expected type bool value, got {type(debug).__name__} type instead"
            )
        if logger not in (False, None, True) and not hasattr(logger, "info"):
            raise TypeError(
                f"logger expected bool or logging.Logger, got {type(logger).__name__}"
            )
        if not isinstance(collect_all, bool):
            raise TypeError(
                f"collect_all expected type bool value, got {type(collect_all).__name__} type instead"
            )
        self.name = name
        self.default = default
        self.doc = doc
        self.debug = debug
        self.logger = False if logger is None else logger
        self.collect_all = collect_all
        self.errors: list[BaseException] = []
        self.annotation = getattr(self, "annotation", None)

    def pre_set(self, obj: Any, value: Any) -> Any:
        return value

    def post_set(self, obj: Any, value: Any) -> Any:
        return value

    def pre_get(self, obj: Any, value: Any) -> Any:
        return value

    def post_get(self, obj: Any, value: Any) -> Any:
        return value

    def pre_delete(self, obj: Any, value: Any) -> Any:
        return value

    def post_delete(self, obj: Any, value: Any) -> Any:
        return value

    def _log(self, level: str, message: str) -> None:
        logger = self.logger
        if logger and logger is not True and hasattr(logger, level):
            getattr(logger, level)(message)

    def _swallow_or_raise(self, err: BaseException) -> None:
        from ux_valio.validators.errors import ValidationErrors

        if isinstance(err, ValidationErrors):
            self.errors.extend(err.errors)
        else:
            self.errors.append(err)
        self._log("error", str(err))
        if self.debug:
            raise err

    def __set_name__(self, owner: type, name: str) -> None:
        # valio@3415c03 valio/descriptor/descriptors.py L134–202:
        # _set_name + _may_set_or_ensure_annotation_match. Fail closed; not debug-swallow.
        # Name mismatch is always AttributeError. A stuck name is a lie.
        try:
            if self.name is None:
                self.name = name
            elif name != self.name:
                raise AttributeError(
                    f"{self.name} != {name}, attribute names did not match"
                )
            self._bind_owner_annotation(owner, name)
        except Exception as err:
            self.errors.append(err)
            raise

    def _bind_owner_annotation(self, owner: type, name: str) -> None:
        annotations = getattr(owner, "__annotations__", None) or {}
        owner_annotation = annotations.get(name)
        if self.annotation is None:
            if owner_annotation is not None:
                self.annotation = owner_annotation
            return
        if owner_annotation is None:
            return
        if not _annotations_agree(self.annotation, owner_annotation):
            raise TypeError(
                f"{owner.__name__}.{self.name}: {_annotation_label(owner_annotation)}"
                f" annotation did not match {type(self).__qualname__}: "
                f"{_annotation_label(self.annotation)}"
            )

    def __set__(self, obj: Any, value: Any) -> None:
        try:
            if value is None and self.default is not None:
                value = self.default() if callable(self.default) else self.default
            value = self.pre_set(obj, value)
            obj.__dict__[self.name] = value
            self.post_set(obj, value)
        except Exception as err:
            self._swallow_or_raise(err)

    def __get__(self, obj: Any, obj_type: type | None = None) -> Any:
        if obj is None:
            return None
        try:
            self.pre_get(obj, self.name)
            return obj.__dict__[self.name]
        except Exception as err:
            self._swallow_or_raise(err)
            return None
        finally:
            try:
                self.post_get(obj, self.name)
            except Exception as post_err:
                self._swallow_or_raise(post_err)

    def __delete__(self, obj: Any) -> None:
        try:
            self.pre_delete(obj, self.name)
            del obj.__dict__[self.name]
            self.post_delete(obj, self.name)
        except Exception as err:
            self._swallow_or_raise(err)

    def __str__(self) -> str:
        return str(self.name)
