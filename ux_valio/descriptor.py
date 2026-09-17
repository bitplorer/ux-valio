# SPDX-License-Identifier: MIT
"""Descriptor lifecycle.

``__set__`` applies ``default`` / ``default_factory`` only when the assigned
value ``is None``. Falsy assigned values ``0`` / ``False`` / ``""`` are kept.
``default=[]`` is the same object on every instance. ``default_factory=`` is
a zero-arg callable invoked per None assignment. Both set is ``TypeError``.
Leftover: a callable ``default=`` is still invoked (valio).

``debug`` falsy swallows exceptions, appends them to ``errors``, and does
not re-raise. ``debug=True`` re-raises. This swallow is KEEP — not a
silent fail-closed flip. ``collect_all`` (default ``False``) is a separate
opt-in: fail-fast remains the door. ``collect_all=True`` continues remaining
concerns and surfaces every failure. Do not overload ``debug`` into collect.

Class access (``obj is None``) returns ``None`` so dataclasses treat the
descriptor as a missing field default and route ``Cls()`` through
``__set__(instance, None)``, which then applies ``default``.

Only the descriptor ``pre_set`` hook return is stored. That hook is the
validate pipeline, not a ``_processors[\"pre_set\"]`` bag. Hang before-store
work on ``add_pre_validator`` / ``add_validator`` / ``add_pre_validator_task``.
``post_set`` / get / delete return values are ignored. ``__get__`` /
``__delete__`` pass ``self.name`` into hooks, not the stored value.
Never-set ``__get__`` / ``__delete__`` with ``debug=True`` raise a named
``AttributeError`` (``Cls.field is not set``), not a bare ``KeyError``.
Debug-falsy still swallows and ``__get__`` reads back ``None``.
``add_*`` may be async. No ``asyncio.run`` in ``__set__``.

Logger default is OFF.

``__set_name__`` is fail-closed on annotation conflict. If both
``validator.annotation`` and the owner class annotation are set and they
disagree, raise ``TypeError``. Owner wins only when the validator annotation
was ``None``. The validator annotation is kept when the owner has none.
Unresolved owner annotations (``str`` / ``ForwardRef``, including
``from __future__ import annotations``) raise ``TypeError`` at bind and are
not copied into the type door. They are not ``eval``'d. Union forms and
list/dict/tuple/set/frozenset aliases are compared with stdlib
``get_origin`` / ``get_args`` (``typing.Union`` and ``X | Y``;
``list[T]`` and ``typing.List[T]``), not typingx / typing_extensions.
"""

from __future__ import annotations

import types
from typing import Any, ForwardRef, Union, get_args, get_origin

_UNSET = object()


class _Opt:
    """One specified-theory: omitted vs caller-set.

    Runtime value is ``.value``. Merge uses ``.specified``.
    ``debug is None`` and logger/collect_all ``_UNSET`` are omitted.
    Explicit ``False`` is specified.
    """

    __slots__ = ("value", "specified")

    def __init__(self, value: Any, specified: bool) -> None:
        self.value = value
        self.specified = specified

    @classmethod
    def omitted(cls, default: Any) -> "_Opt":
        return cls(default, False)

    @classmethod
    def set(cls, value: Any) -> "_Opt":
        return cls(value, True)


def merge_opt(attr: str, *opts: _Opt) -> _Opt:
    present = [opt for opt in opts if opt.specified]
    if not present:
        return opts[0] if opts else _Opt.omitted(None)
    first = present[0]
    for opt in present[1:]:
        if opt.value != first.value:
            raise TypeError(
                f"composed validators have conflicting {attr}: "
                f"{first.value!r} vs {opt.value!r}"
            )
    return first


def opt_of(item: Any, attr: str, omitted_default: Any = None) -> _Opt:
    opts = getattr(item, "_opts", None)
    if isinstance(opts, dict) and attr in opts:
        return opts[attr]
    value = getattr(item, attr, omitted_default)
    return _Opt(value, value is not omitted_default)


_CONTAINER_ORIGINS = (list, dict, tuple, set, frozenset)


def _annotation_identity(annotation: Any) -> Any:
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


def _is_unresolved_annotation(annotation: Any) -> bool:
    return isinstance(annotation, (str, ForwardRef))


class Property:
    """Data descriptor used as a dataclass field default (Door A)."""

    def __init__(
        self,
        name: str | None = None,
        default: Any = None,
        default_factory: Any = None,
        doc: str | None = None,
        debug: bool | None = None,
        logger: Any = _UNSET,
        collect_all: Any = _UNSET,
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
        if logger is _UNSET:
            logger_opt = _Opt.omitted(False)
        else:
            if logger not in (False, None, True) and not hasattr(logger, "info"):
                raise TypeError(
                    f"logger expected bool or logging.Logger, got {type(logger).__name__}"
                )
            logger_opt = _Opt.set(False if logger is None else logger)
        if collect_all is _UNSET:
            collect_opt = _Opt.omitted(False)
        else:
            if not isinstance(collect_all, bool):
                raise TypeError(
                    f"collect_all expected type bool value, got {type(collect_all).__name__} type instead"
                )
            collect_opt = _Opt.set(collect_all)
        if default_factory is not None and not callable(default_factory):
            raise TypeError(
                f"default_factory expected a callable, got {type(default_factory).__name__}"
            )
        if default is not None and default_factory is not None:
            raise TypeError("default and default_factory cannot both be set")
        self.name = name
        self.default = default
        self.default_factory = default_factory
        self.doc = doc
        self.debug = debug
        self.logger = logger_opt.value
        self.collect_all = collect_opt.value
        self._opts = {
            "debug": _Opt.set(debug) if debug is not None else _Opt.omitted(None),
            "default": _Opt.set(default) if default is not None else _Opt.omitted(None),
            "default_factory": (
                _Opt.set(default_factory) if default_factory is not None else _Opt.omitted(None)
            ),
            "doc": _Opt.set(doc) if doc is not None else _Opt.omitted(None),
            "logger": logger_opt,
            "collect_all": collect_opt,
        }
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
        if owner_annotation is not None and _is_unresolved_annotation(owner_annotation):
            raise TypeError(
                f"{owner.__name__}.{self.name}: {_annotation_label(owner_annotation)}"
                " annotation is unresolved (string / ForwardRef); "
                "not copied into the type door"
            )
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
            if value is None:
                if self.default_factory is not None:
                    value = self.default_factory()
                elif self.default is not None:
                    value = self.default() if callable(self.default) else self.default
            value = self.pre_set(obj, value)
            obj.__dict__[self.name] = value
            self.errors.clear()
            self.post_set(obj, value)
        except Exception as err:
            self._swallow_or_raise(err)

    def _missing_attribute(self, obj: Any) -> AttributeError:
        return AttributeError(f"{type(obj).__name__}.{self.name} is not set")

    def __get__(self, obj: Any, obj_type: type | None = None) -> Any:
        if obj is None:
            return None
        try:
            self.pre_get(obj, self.name)
            try:
                return obj.__dict__[self.name]
            except KeyError:
                raise self._missing_attribute(obj) from None
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
            try:
                del obj.__dict__[self.name]
            except KeyError:
                raise self._missing_attribute(obj) from None
            self.post_delete(obj, self.name)
        except Exception as err:
            self._swallow_or_raise(err)

    def __str__(self) -> str:
        return str(self.name)
