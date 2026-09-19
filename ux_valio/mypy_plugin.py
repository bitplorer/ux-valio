# SPDX-License-Identifier: MIT
"""Make ``name: str = StringValidator()`` type-check.

``dataclasses.field`` returns ``T``. A class constructor cannot. This plugin
types named-facade construction as ``Any`` so it assigns to ``str`` / ``int``
and still supports ``&`` / ``|``. Enable:
``plugins = ["ux_valio.mypy_plugin"]``.
"""

from __future__ import annotations

from mypy.nodes import TypeInfo
from mypy.plugin import FunctionContext, Plugin
from mypy.types import AnyType, Type, TypeOfAny

_PROPERTY = "ux_valio.descriptor.Property"
_SKIP = {
    _PROPERTY,
    "ux_valio.validators.base.ValidateProperty",
    "ux_valio.validators.base.AllOf",
    "ux_valio.validators.base.AnyOf",
    "ux_valio.validators.hooks.HookHost",
}


def _ctor_as_any(ctx: FunctionContext) -> Type:
    return AnyType(TypeOfAny.special_form)


class UxValioPlugin(Plugin):
    def get_function_hook(self, fullname: str):
        if fullname in _SKIP:
            return None
        sym = self.lookup_fully_qualified(fullname)
        if sym is None or not isinstance(sym.node, TypeInfo):
            return None
        if any(base.fullname == _PROPERTY for base in sym.node.mro):
            return _ctor_as_any
        return None


def plugin(version: str) -> type[Plugin]:
    return UxValioPlugin
