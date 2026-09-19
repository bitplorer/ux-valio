# Honesty (KEEP)

These are the runtime contracts. The *why* lives in
[choices](choices.md). Performance of the specified path lives in
[performance](performance.md).

Omitted `debug` is `True` (re-raise). `debug=False` swallows, appends to
`errors`, and leaves the attribute unset so later reads are `None`.
Never-set `__get__` / `__delete__` with debug on raises a named
`AttributeError` (`Cls.field is not set`), not a bare `KeyError`.
This swallow is KEEP. Pass `debug=False` to opt in.

Omitted `collect_all` is `True`: remaining concerns continue. One failure
re-raises as itself; two or more surface as `ValidationErrors` (debug on)
or as multiple entries on `errors` (debug off). `collect_all=False` is
fail-fast. Do not overload `debug` into collect-all.

```python
n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)
```

`logger` defaults **OFF** (`False`). `logger=True` binds a stdlib
`logging.Logger` at `__set_name__` named `module.qualname.field`.
No files, no `logs/` directory. `logger=None` is OFF, not valio's
None=on. Get/set/delete log at info; failures at error. A field-level
logger is the usage pattern Pydantic does not have.

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
`default=[]` is the same list on every instance. `default_factory=` is a
zero-arg callable invoked on each None assignment (dataclass-shaped, still
the descriptor — not a Field twin). Setting both is `TypeError`.
A callable `default=` is still invoked (`default=list` already built a
new list); prefer `default_factory=list` when the intent is per-instance.

The field stores on `instance.__dict__`. Explicit `__slots__` that include
the field TypeError at bind. A slots-only class (no `__dict__` in the MRO)
TypeErrors at bind even when the field name is not a slot. A child that
does not define `__slots__` still has `__dict__`. `@dataclass(slots=True)`
is unsupported: dataclass replaces the descriptor after bind, and
validation would not run. `@dataclass(frozen=True)` works: dataclass
intercepts assign/delete with `FrozenInstanceError`; `__init__` still
runs the field descriptor.

`__get__` `post_get` runs in `finally`. A failing post_get is recorded; it
does not replace an in-flight never-set `AttributeError` when `debug=True`.
