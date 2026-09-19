# Validator

`Validator` is the descriptor you put on a field when there is **no**
named facade for that type. `IntegerValidator` / `StringValidator` are
the same object with `annotation` already set. `Validator[int]`
declares the stored type. Named facades specialize it
(`IntegerValidator` is `Validator[int]`).

**Where:** a dataclass column, a TypedDict key, a plain-class attribute,
or a Protocol port (`users: UserStore = Validator[UserStore](...)`).

```python
n: int = IntegerValidator(min_value=0)
rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
```

`rank` uses `Validator` because `in_choice` is a closed string list, not
a new store type. `n` uses `IntegerValidator` because the store is `int`.

Specified path units bind at construct (`_active_units`): type always;
`min_value` / `pattern` / `reassign=False` / … only when that bound is
set. Mutating those kwargs after `__init__` does not rebuild the path —
pass them at construct. A subclass that replaces `validation_path`
keeps its declared units. An unknown validation-path unit raises
`ValueError`, not `KeyError`.

## Constructor

| kwarg | omitted | meaning |
|---|---|---|
| `annotation` | from `Validator[T]` or owner | type door |
| `required` | `False` | `None` rejected when True |
| `default` | unset | used when assigned `None`; falsy `0`/`False`/`""` stay |
| `default_factory` | unset | zero-arg callable per None assignment; `not a Field twin` |
| `debug` | `True` | re-raise; `False` swallows |
| `collect_all` | `True` | continue remaining concerns |
| `logger` | `False` | `True` → `module.qualname.field` |
| `min_length` / `max_length` | unset | sized values |
| `min_value` / `max_value` | unset | inclusive |
| `gt` / `lt` | unset | exclusive |
| `multiple_of` | unset | remainder; `0` accepts only `0` |
| `pattern` | unset | `PatternType` / compiled / str |
| `in_choice` / `not_in_choice` | unset | skip `None`; must be a `Container` at construct |
| `reassign` | `True` | `False` rejects a second set |
| `name` | from `__set_name__` | field name for errors |

`default=` and `default_factory=` together is `TypeError`.
`default_factory=` is a zero-arg callable invoked on each None
assignment (dataclass-shaped, still the descriptor — not a Field twin).

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
