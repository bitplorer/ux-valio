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

Class access (``obj is None``) returns the descriptor, so
``Cls.field.add_process_pre_validate`` works after the class exists — hang
hooks on the field name, no outer ``username_field`` twin. Dataclass
``getattr`` then sees the descriptor as the field default; ``__set__``
treats ``value is self`` as unset and applies ``default`` /
``default_factory``. Do not invent a Field mixin. Class access also
records ``obj_type`` as ``_owner``, so a shared descriptor's
``Person.aadhaar.add_*`` uses Person (not the last ``__set_name__``).

``@dataclass(frozen=True)`` works: dataclass ``__setattr__`` /
``__delattr__`` raise ``FrozenInstanceError`` before the descriptor
mutates. ``@dataclass(slots=True)`` stays unsupported.

Only the descriptor ``pre_set`` hook return is stored. That hook is the
validate pipeline, not a ``_processors[\"pre_set\"]`` bag. Hang before-store
work on ``add_process_pre_validate`` / ``add_validator`` / ``add_task_pre_validate``.
``post_set`` / get / delete return values are ignored. ``__get__`` /
``__delete__`` pass ``self.name`` into hooks, not the stored value.
Never-set ``__get__`` / ``__delete__`` with ``debug=True`` raise a named
``AttributeError`` (``Cls.field is not set``), not a bare ``KeyError``.
Debug-falsy still swallows and ``__get__`` reads back ``None``.
``add_*`` may be async. No ``asyncio.run`` in ``__set__``.

``post_get`` in ``__get__`` ``finally`` must not replace an in-flight
exception: record it, keep the original raise / swallow.

Stores on ``instance.__dict__``. Explicit ``__slots__`` that
include the field TypeError at bind. A slots-only class (no ``__dict__``
in the MRO) TypeErrors at bind even when the field name is not itself a
slot — get/delete would otherwise see a bare ``AttributeError``. Look at
``owner.__dict__["__slots__"]``, not inherited ``getattr`` (a child that
does not define slots still has ``__dict__``). ``@dataclass(slots=True)``
replaces the descriptor after bind — unsupported (validation would not run).


Logger default is OFF (``False``). ``logger=True`` binds a stdlib
``logging.Logger`` at ``__set_name__`` named ``module.qualname.field``.
No files, no ``logs/`` directory — valio wrote files; pass your own
``logging.Logger`` for that. ``logger=None`` is OFF, not valio's None=on.
Get/set/delete log at info; failures at error. Specified-theory still
sees ``True`` after bind (runtime logger is a separate object).

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

import logging
import types
from dataclasses import dataclass, fields
from typing import Any, ForwardRef, Generic, TypeVar, Union, get_args, get_origin, overload

from ux_valio.errors import ValidationErrors

_UNSET = object()
_StoreT = TypeVar("_StoreT")


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

    @classmethod
    def merge(cls, *opts: "_Opt", what: str | None = None) -> "_Opt":
        """One specified value, or TypeError on conflict."""
        present = [opt for opt in opts if opt.specified]
        if not present:
            return opts[0] if opts else cls.omitted(None)
        first = present[0]
        for opt in present[1:]:
            if opt.value != first.value:
                label = what if what is not None else "values"
                raise TypeError(
                    f"composed validators have conflicting {label}: "
                    f"{first.value!r} vs {opt.value!r}"
                )
        return first

    def keeps_nesting(self, members: "_Opt") -> bool:
        """True when this descriptor's spec should not flatten into members."""
        if self.specified and not members.specified:
            return True
        if self.specified and self.value != members.value:
            return True
        if not self.specified and members.specified:
            return False
        return self.value != members.value


@dataclass(slots=True)
class _Opts:
    """Specified-theory for one descriptor. Fields are the source of truth.

    Add a field here and ``merge`` / ``overlay`` / ``keeps_nesting`` follow.
    ``from_call`` is the constructor (``debug=``, ``logger=``, …).
    """

    debug: _Opt
    default: _Opt
    default_factory: _Opt
    doc: _Opt
    logger: _Opt
    collect_all: _Opt

    @classmethod
    def from_call(
        cls,
        *,
        debug: bool | None = None,
        default: Any = None,
        default_factory: Any = None,
        doc: str | None = None,
        logger: Any = _UNSET,
        collect_all: Any = _UNSET,
    ) -> "_Opts":
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
        return cls(
            debug=_Opt.set(debug) if debug is not None else _Opt.omitted(None),
            default=_Opt.set(default) if default is not None else _Opt.omitted(None),
            default_factory=(
                _Opt.set(default_factory) if default_factory is not None else _Opt.omitted(None)
            ),
            doc=_Opt.set(doc) if doc is not None else _Opt.omitted(None),
            logger=logger_opt,
            collect_all=collect_opt,
        )

    @classmethod
    def merge(cls, *rows: "_Opts") -> "_Opts":
        merged: dict[str, _Opt] = {}
        for field in fields(cls):
            merged[field.name] = _Opt.merge(
                *(getattr(row, field.name) for row in rows),
                what=field.name,
            )
        return cls(**merged)

    def overlay(
        self,
        *,
        debug: bool | None = None,
        default: Any = None,
        default_factory: Any = None,
        doc: str | None = None,
        logger: Any = _UNSET,
        collect_all: Any = _UNSET,
    ) -> "_Opts":
        incoming = type(self).from_call(
            debug=debug,
            default=default,
            default_factory=default_factory,
            doc=doc,
            logger=logger,
            collect_all=collect_all,
        )
        merged: dict[str, _Opt] = {}
        for field in fields(self):
            incoming_opt = getattr(incoming, field.name)
            merged[field.name] = (
                incoming_opt if incoming_opt.specified else getattr(self, field.name)
            )
        result = type(self)(**merged)
        if result.default.specified and result.default_factory.specified:
            raise TypeError("default and default_factory cannot both be set")
        return result

    def keeps_nesting(self, members: "_Opts") -> bool:
        return any(
            getattr(self, field.name).keeps_nesting(getattr(members, field.name))
            for field in fields(self)
        )


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


def _union_member_ids(annotation: Any) -> frozenset[Any] | None:
    ident = _annotation_identity(annotation)
    if isinstance(ident, tuple) and ident and ident[0] is Union:
        return ident[1]
    return None


def _annotations_agree(left: Any, right: Any) -> bool:
    """Owner (right) matches validator (left), or is a member/subset of it.

    Coercing facades declare ``T | str``. Owner ``T``, ``str``, or ``T | str``
    all bind. Owner wider than validator (``int | str`` vs ``int``) does not.
    """
    if left is right:
        return True
    left_id = _annotation_identity(left)
    right_id = _annotation_identity(right)
    if left_id == right_id:
        return True
    left_u = _union_member_ids(left)
    if left_u is None:
        return False
    right_u = _union_member_ids(right)
    if right_u is not None:
        return right_u <= left_u
    return right_id in left_u


def _annotation_label(annotation: Any) -> str:
    if isinstance(annotation, str):
        return repr(annotation)
    return annotation.__name__ if hasattr(annotation, "__name__") else str(annotation)


def _is_unresolved_annotation(annotation: Any) -> bool:
    return isinstance(annotation, (str, ForwardRef))


def _is_unconstrained_typevar(annotation: Any) -> bool:
    """Unconstrained TypeVar is typing-only. Runtime cannot specialize per T."""
    return (
        isinstance(annotation, TypeVar)
        and not annotation.__constraints__
        and annotation.__bound__ is None
    )



class Property(Generic[_StoreT]):
    """Data descriptor used as a dataclass field default.

    ``Validator[int]`` is the stored-type subscript (one argument). It
    fills ``annotation`` when the class did not declare one. Unconstrained
    TypeVars are typing-only and are not copied onto the descriptor.
    """

    def __init__(
        self,
        name: str | None = None,
        default: Any = None,
        default_factory: Any = None,
        doc: str | None = None,
        debug: bool | None = None,
        logger: Any = _UNSET,
        collect_all: Any = _UNSET,
        *,
        _opts: _Opts | None = None,
    ) -> None:
        if name is not None and not isinstance(name, str):
            raise TypeError(
                f"name expected type str value, got {type(name).__name__} type instead"
            )
        if _opts is None:
            _opts = _Opts.from_call(
                debug=debug,
                default=default,
                default_factory=default_factory,
                doc=doc,
                logger=logger,
                collect_all=collect_all,
            )
        self.name = name
        self.default = _opts.default.value
        self.default_factory = _opts.default_factory.value
        self.doc = _opts.doc.value
        self.debug = _opts.debug.value
        self.logger = _opts.logger.value
        self.collect_all = _opts.collect_all.value
        self._opts = _opts
        self.errors: list[BaseException] = []
        self.annotation = getattr(self, "annotation", None)
        self._owner: type | None = None

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

    def _bind_field_logger(self, owner: type, name: str) -> None:
        """``logger=True`` becomes a stdlib logger named for this field.

        Specified-theory ``_opts.logger`` stays ``True``. No FileHandler.
        """
        if self.logger is True:
            self.logger = logging.getLogger(
                f"{owner.__module__}.{owner.__qualname__}.{name}"
            )

    def _log(self, level: str, message: str) -> None:
        logger = self.logger
        if logger is True or not logger:
            return
        sink = getattr(logger, level, None)
        if callable(sink):
            sink(message)

    def _record_error(self, err: BaseException) -> None:
        if isinstance(err, ValidationErrors):
            self.errors.extend(err.errors)
        else:
            self.errors.append(err)
        self._log("error", str(err))

    def _swallow_or_raise(self, err: BaseException) -> None:
        self._record_error(err)
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
            self._owner = owner
            self._reject_slots_without_dict(owner, name)
            self._take_subscript_annotation()
            self._bind_owner_annotation(owner, name)
            self._bind_field_logger(owner, name)
        except Exception as err:
            self.errors.append(err)
            raise

    def _reject_slots_without_dict(self, owner: type, name: str) -> None:
        """Fail-closed when the field cannot store on the instance.

        Only this class's ``__slots__`` can name the field (inherited
        ``getattr(owner, "__slots__")`` false-positives a child that still
        has ``__dict__``). A slots-only MRO with no ``__dict__`` member
        cannot store any descriptor field.
        """
        own_slots = owner.__dict__.get("__slots__")
        if own_slots is not None and name in type(self)._slot_names(own_slots):
            raise TypeError(
                f"{owner.__name__}.{name}: field stores on instance __dict__; "
                "__slots__ replaces it and drops validation"
            )
        if type(self)._owner_omits_instance_dict(owner):
            raise TypeError(
                f"{owner.__name__}.{name}: field stores on instance __dict__; "
                "__slots__ without '__dict__' drops storage"
            )

    @staticmethod
    def _slot_names(slots: Any) -> tuple[str, ...]:
        if isinstance(slots, str):
            return (slots,)
        return tuple(slots)

    @staticmethod
    def _owner_omits_instance_dict(owner: type) -> bool:
        """True when instances of ``owner`` have no ``__dict__`` (slots-only MRO)."""
        saw_slots = False
        for cls in owner.__mro__:
            if cls is object:
                continue
            if "__slots__" not in cls.__dict__:
                return False
            if "__dict__" in Property._slot_names(cls.__dict__["__slots__"]):
                return False
            saw_slots = True
        return saw_slots

    def _take_subscript_annotation(self) -> None:
        """``Validator[int]()`` fills annotation from ``__orig_class__``.

        ``GenericAlias.__call__`` sets ``__orig_class__`` after ``__init__``.
        Unconstrained TypeVars stay typing-only. A declared class annotation
        (``IntegerValidator.annotation = int``) must agree with the subscript.
        """
        orig = getattr(self, "__orig_class__", None)
        if orig is None:
            return
        args = get_args(orig)
        if not args:
            return
        if len(args) != 1:
            raise TypeError(
                f"{type(self).__qualname__}[...] takes one stored-type argument"
            )
        subscript = args[0]
        if _is_unconstrained_typevar(subscript):
            return
        if self.annotation is None:
            self.annotation = subscript
            return
        if not _annotations_agree(self.annotation, subscript):
            raise TypeError(
                f"{type(self).__qualname__}[{_annotation_label(subscript)}] "
                f"did not match {type(self).__qualname__}: "
                f"{_annotation_label(self.annotation)}"
            )

    def _bind_owner_annotation(self, owner: type, name: str) -> None:
        annotations = getattr(owner, "__annotations__", None) or {}
        owner_annotation = annotations.get(name)
        if owner_annotation is not None and _is_unresolved_annotation(owner_annotation):
            raise TypeError(
                f"{owner.__name__}.{self.name}: {_annotation_label(owner_annotation)}"
                " annotation is unresolved (string / ForwardRef); "
                "not copied onto the descriptor"
            )
        if owner_annotation is not None and _is_unconstrained_typevar(owner_annotation):
            owner_annotation = None
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

    def _require_instance_dict(self, obj: Any) -> dict[str, Any]:
        instance_dict = getattr(obj, "__dict__", None)
        if instance_dict is None:
            raise TypeError(
                f"{type(obj).__name__}.{self.name} has no instance __dict__; "
                "slots-only classes cannot store this field"
            )
        return instance_dict

    def _store_on_instance(self, obj: Any, value: Any) -> None:
        name = self.name
        if name is None:
            raise TypeError(f"{type(self).__qualname__} is not bound to a class")
        self._require_instance_dict(obj)[name] = value

    def _read_from_instance(self, obj: Any) -> Any:
        name = self.name
        if name is None:
            raise TypeError(f"{type(self).__qualname__} is not bound to a class")
        try:
            return self._require_instance_dict(obj)[name]
        except KeyError:
            raise self._missing_attribute(obj) from None

    def _drop_from_instance(self, obj: Any) -> None:
        name = self.name
        if name is None:
            raise TypeError(f"{type(self).__qualname__} is not bound to a class")
        try:
            del self._require_instance_dict(obj)[name]
        except KeyError:
            raise self._missing_attribute(obj) from None

    def __set__(self, obj: Any, value: Any) -> None:
        try:
            if value is self:
                value = None
            if value is None:
                if self.default_factory is not None:
                    value = self.default_factory()
                elif self.default is not None:
                    value = self.default() if callable(self.default) else self.default
            value = self.pre_set(obj, value)
            self._store_on_instance(obj, value)
            self.errors.clear()
            self._log("info", f"{type(obj).__name__}.{self.name}: set")
            self.post_set(obj, value)
        except Exception as err:
            self._swallow_or_raise(err)

    def _missing_attribute(self, obj: Any) -> AttributeError:
        return AttributeError(f"{type(obj).__name__}.{self.name} is not set")

    @overload
    def __get__(self, obj: None, obj_type: type | None = None) -> Property[_StoreT]: ...

    @overload
    def __get__(self, obj: object, obj_type: type | None = None) -> _StoreT: ...

    def __get__(self, obj: Any, obj_type: type | None = None) -> Any:
        if obj is None:
            if obj_type is not None:
                self._owner = obj_type
            return self
        in_flight: BaseException | None = None
        try:
            self.pre_get(obj, self.name)
            value = self._read_from_instance(obj)
            self._log("info", f"{type(obj).__name__}.{self.name}: get")
            return value
        except Exception as err:
            in_flight = err
            self._swallow_or_raise(err)
            return None
        finally:
            try:
                self.post_get(obj, self.name)
            except Exception as post_err:
                if in_flight is not None:
                    # Keep the original raise / swallow. Do not replace it.
                    self._record_error(post_err)
                else:
                    self._swallow_or_raise(post_err)

    def __delete__(self, obj: Any) -> None:
        try:
            self.pre_delete(obj, self.name)
            self._drop_from_instance(obj)
            self._log("info", f"{type(obj).__name__}.{self.name}: delete")
            self.post_delete(obj, self.name)
        except Exception as err:
            self._swallow_or_raise(err)

    def __str__(self) -> str:
        return str(self.name)
