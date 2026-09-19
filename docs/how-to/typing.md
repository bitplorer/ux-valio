# Typing

The taught annotation is the **store type**, not the validator:

```python
name: str = StringValidator(max_length=50)
n: int = IntegerValidator(min_value=0)
```

Runtime the instance sees `str` / `int`. Construction is `Any` to type
checkers (`ValidateProperty.__new__`; mypy via
`plugins = ["ux_valio.mypy_plugin"]`) so the assignment is legal. No
per-type mixin (`AsStr`, `AsInt`, `AsUser`).

## `Validator[T]`

`Validator[int]` is the same descriptor with the stored type on it.
Use it on a plain class (no field annotation) or next to `n: int` — the
two must agree or bind TypeErrors. `IntegerValidator` is already
`Validator[int]`.

```python
class Stats:
    n = Validator[int](min_value=0)
```

A new store type:

```python
class AccountValidator(Validator[Account]):
    annotation = Account
```

Optional needs `| None` on **both** sides. A subclass owner
(`Admin(Account)`) binds (`is_subclass_of` at bind, `is_instance_of` at
set). `uuid.UUID | str` (and the same shape on Date / Path / DateTime)
is the coerce-from-string owner.

An unconstrained `TypeVar` (`item: T = Validator()` on a generic class)
is typing-only; runtime cannot specialize one descriptor per `Box[int]`
/ `Box[str]`. Bound TypeVars still copy into the type door.

## What type checkers will not see

- Postponed annotations (`from __future__ import annotations`) stay
  strings. Bind TypeErrors rather than silently skip. Drop postponed
  annotations on these fields.
- `name: Validator[str] = StringValidator()` peels to the store type.
- Pyright/Pylance without the plugin still accept construction as `Any`
  from `__new__`. The plugin is for mypy.
- Protocol ports need `@runtime_checkable` for the **runtime** type
  door. The type checker already treats Protocol structurally.

## Plugin

```toml
# mypy.ini / pyproject.toml
[tool.mypy]
plugins = ["ux_valio.mypy_plugin"]
```
