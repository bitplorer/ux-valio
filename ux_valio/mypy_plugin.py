# SPDX-License-Identifier: MIT
"""mypy: a ValidateProperty constructor is assignable to the field annotation.

Pylance/pyright already honor ``ValidateProperty.__new__ -> Any``. mypy
ignores source ``__new__``, so this hook returns Any for every subclass
constructor — ``str``, ``User``, ``Database``, not a per-type mixin.
"""

from __future__ import annotations

from typing import Callable

from mypy.nodes import TypeInfo
from mypy.plugin import FunctionContext, Plugin
from mypy.types import AnyType, Type, TypeOfAny

_VALIDATE = "ux_valio.validators.base.ValidateProperty"


class UxValioPlugin(Plugin):
    def get_function_hook(
        self, fullname: str
    ) -> Callable[[FunctionContext], Type] | None:
        info = self._info(fullname)
        if info is None:
            return None
        for base in info.mro:
            if base.fullname == _VALIDATE:
                return _as_any
        return None

    def _info(self, fullname: str) -> TypeInfo | None:
        sym = self.lookup_fully_qualified(fullname)
        if sym is None:
            return None
        node = getattr(sym, "node", None)
        return node if isinstance(node, TypeInfo) else None


def _as_any(ctx: FunctionContext) -> Type:
    return AnyType(TypeOfAny.special_form)


def plugin(version: str) -> type[Plugin]:
    return UxValioPlugin
