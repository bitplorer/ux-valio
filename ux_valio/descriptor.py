# SPDX-License-Identifier: MIT
"""Descriptor lifecycle (A9 unit 1).

``__set__`` applies ``default`` only when the assigned value ``is None``
(Soft #2). Falsy assigned values ``0`` / ``False`` / ``""`` are kept.

``debug`` falsy swallows exceptions, appends them to ``errors``, and does
not re-raise. ``debug=True`` re-raises. This swallow is KEEP — not a
silent fail-closed flip.

Class access (``obj is None``) returns ``None`` so dataclasses treat the
descriptor as a missing field default and route ``Cls()`` through
``__set__(instance, None)``, which then applies ``default``.

Only the ``pre_set`` return is stored. ``post_set`` / get / delete return
values are ignored. ``__get__`` / ``__delete__`` pass ``self.name`` into
hooks, not the stored value.

Logger default is OFF.
"""

from __future__ import annotations

from typing import Any


class Property:
    """Data descriptor used as a dataclass field default (Door A)."""

    def __init__(
        self,
        name: str | None = None,
        default: Any = None,
        doc: str | None = None,
        debug: bool | None = None,
        logger: Any = False,
        **kwargs: Any,
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
        self.name = name
        self.default = default
        self.doc = doc
        self.debug = debug
        self.logger = False if logger is None else logger
        self.errors: list[BaseException] = []
        self.annotation = getattr(self, "annotation", None)
        self.kwargs = kwargs

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
        self.errors.append(err)
        self._log("error", str(err))
        if self.debug:
            raise err

    def __set_name__(self, owner: type, name: str) -> None:
        if self.name is None:
            self.name = name
        annotations = getattr(owner, "__annotations__", None) or {}
        owner_annotation = annotations.get(name)
        if self.annotation is None and owner_annotation is not None:
            self.annotation = owner_annotation
        elif owner_annotation is not None:
            self.annotation = owner_annotation

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
