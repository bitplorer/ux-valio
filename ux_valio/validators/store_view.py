# SPDX-License-Identifier: MIT
"""TYPE_CHECKING view: a named facade *is* its store type.

Runtime these bases are empty. Type checkers see ``StringValidator <: str``,
so ``name: str = StringValidator()`` is the same annotation on both sides.
``__set_name__`` still fail-closed if the owner annotation disagrees.
"""

from __future__ import annotations

import datetime
import decimal
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    class AsStr(str):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsInt(int):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsBool(bool):  # type: ignore[misc]
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsFloat(float):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsBytes(bytes):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsDecimal(decimal.Decimal):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsDate(datetime.date):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsDateTime(datetime.datetime):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    class AsUUID(uuid.UUID):
        def __new__(cls, *args: Any, **kwargs: Any) -> Any: ...
        def __init__(self, *args: Any, **kwargs: Any) -> None: ...

else:
    class AsStr:
        __slots__ = ()

    class AsInt:
        __slots__ = ()

    class AsBool:
        __slots__ = ()

    class AsFloat:
        __slots__ = ()

    class AsBytes:
        __slots__ = ()

    class AsDecimal:
        __slots__ = ()

    class AsDate:
        __slots__ = ()

    class AsDateTime:
        __slots__ = ()

    class AsUUID:
        __slots__ = ()
