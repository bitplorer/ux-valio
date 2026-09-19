# Validator

`Validator` is the descriptor field default that composes concern
leaves. `Validator[int]` declares the stored type. Named facades
specialize it (`IntegerValidator` is `Validator[int]`).

```python
n: int = IntegerValidator(min_value=0)
rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
```

Specified path units bind at construct (`_active_units`): type always;
`min_value` / `pattern` / `reassign=False` / … only when that bound is
set. Mutating those kwargs after `__init__` does not rebuild the path —
pass them at construct. A subclass that replaces `validation_path`
keeps its declared units. An unknown validation-path unit raises
`ValueError`, not `KeyError`.

## Leaves

Min/max length and value leaves (`MinLengthValidator`,
`MaxLengthValidator`, `MinValueValidator`, `MaxValueValidator`) are
public building blocks, with `TypeValidator`, `RequiredValidator`,
`PatternValidator`, `ChoiceValidator`, `ReassignValidator`,
`MultipleValidator`, `ValueValidator`. `AttributeValidator` is **not**
shipped. Check object attributes at the call site or with `validator`.

List / dictionary / set / tuple collection facades are not
shipped; `list[T]` / `dict[K, V]` membership is the type check.

## Bounds

Bound `0` is specified: `min_value`/`max_value` inclusive, `gt`/`lt`
exclusive, `multiple_of` is remainder, `multiple_of=0` accepts only `0`.
`in_choice` / `not_in_choice` skip `None` (optional unset). A string used
as `in_choice` must not TypeError on that skip.

`post_validate` may transform after checks. If the field has an
annotation, the stored value must still match it. Named facades
re-check their extra on the to-store value. `AllOf` re-checks member
named extras. `AnyOf` still has to match one alternative. Untyped
`Validator()` does not gate. Path bounds on AllOf / unnamed facades are
not re-run. Custom `validator` callables are not re-run.

A new store type is a subclass and an `annotation`. Optional needs
`| None` on **both** sides — `Account` vs `Account | None` is a conflict.
A subclass owner (`Admin(Account)`) binds (`is_subclass_of` at bind,
`is_instance_of` at set).

```python
class Account:
    ...

class AccountValidator(Validator[Account]):
    annotation = Account | None

@dataclass
class Row:
    owner: Account | None = AccountValidator(default=None)
```

Owner annotations that are still strings or `ForwardRef` (including
`from __future__ import annotations`) fail at class body with
`TypeError`. Drop postponed annotations on these fields, or the bind
stays closed. Typed facades conflict with `int | None` / `int | str` at
class body. Use `Validator()` for optional/union fields, or `|` AnyOf
of matching facades.
