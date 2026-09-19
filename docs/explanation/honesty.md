# Honesty (KEEP)

These are the runtime contracts. The *why* lives in
[choices](choices.md). Performance of the specified path lives in
[performance](performance.md).

## Failures: raise or swallow

Omitted `debug` is `True` (re-raise). That is the default you want on a
form: bad input is an exception the service maps to an HTTP 400.

`debug=False` swallows, appends to `errors`, and leaves the attribute
unset so later reads are `None`. Use it only when you are collecting a
batch of problems yourself and will inspect `field.errors`. Never-set
`__get__` / `__delete__` with debug on raises a named `AttributeError`
(`Cls.field is not set`), not a bare `KeyError`.
This swallow is KEEP. Pass `debug=False` to opt in.

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator

@dataclass
class Count:
    n: int = IntegerValidator(min_value=0, debug=False)

row = Count(n=-1)
assert row.n is None          # swallowed
# Count.__dict__["n"].errors  # the failure is here
```

## Several concerns, one field

Omitted `collect_all` is `True`: remaining concerns continue. One failure
re-raises as itself; two or more surface as `ValidationErrors` (debug on)
or as multiple entries on `errors` (debug off). `collect_all=False` is
fail-fast. Do not overload `debug` into collect-all.

```python
n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)
```

`n=-3` fails both `min_value` and `multiple_of` → `ValidationErrors`.
`n=3` fails only `multiple_of` → a single `ValueError`. This is
**per-field**. A later field in the dataclass is not reached once an
earlier field raises — that is generated `__init__` order.

`examples/signup.py` uses this on `seats`.

## Logging

`logger` defaults **OFF** (`False`). `logger=True` binds a stdlib
`logging.Logger` at `__set_name__` named `module.qualname.field`.
No files, no `logs/` directory. `logger=None` is OFF, not valio's
None=on. Get/set/delete log at info; failures at error. A field-level
logger is the usage pattern Pydantic does not have.

The stored value is **not** in the message. Pass your own
`logging.Logger` when you want a `FileHandler`. Full what / where /
how, compose conflicts, `debug=False` + logger, and a runnable form:
[Field-level logging](../how-to/logging.md), `examples/field_logging.py`.

Turn it on in development when you need to see which field assigned.
Leave it off on a hot path ([performance](performance.md)).

## Defaults and falsy values

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
A quantity of `0` is in stock-empty, not “please use the default 1”.

`default=[]` is the same list on every instance. `default_factory=` is a
zero-arg callable invoked on each None assignment (dataclass-shaped, still
the descriptor — not a Field twin). Setting both is `TypeError`.
A callable `default=` is still invoked (`default=list` already built a
new list); prefer `default_factory=list` when the intent is per-instance.

```python
from uuid import uuid4
from ux_valio import UUIDValidator

account_id = UUIDValidator(default_factory=uuid4)  # new id per None
```

## Slots and frozen

The field stores on `instance.__dict__`. Explicit `__slots__` that include
the field TypeError at bind. A slots-only class (no `__dict__` in the MRO)
TypeErrors at bind even when the field name is not a slot. A child that
does not define `__slots__` still has `__dict__`. `@dataclass(slots=True)`
is unsupported: dataclass replaces the descriptor after bind, and
validation would not run. `@dataclass(frozen=True)` works: dataclass
intercepts assign/delete with `FrozenInstanceError`; `__init__` still
runs the field descriptor.

Use `frozen=True` for value objects you construct once. Do not use
`slots=True` with these descriptors.

`__get__` `post_get` runs in `finally`. A failing post_get is recorded; it
does not replace an in-flight never-set `AttributeError` when `debug=True`.
