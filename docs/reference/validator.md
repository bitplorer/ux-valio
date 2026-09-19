# Validator

`Validator` is the descriptor you put on a field when there is **no**
named facade for that type. `IntegerValidator` / `StringValidator` are
the same object with `annotation` already set. `Validator[int]`
declares the stored type. Named facades specialize it
(`IntegerValidator` is `Validator[int]`).

**Where:** a dataclass column, a TypedDict key, a plain-class attribute,
or a Protocol port (`users: UserStore = Validator[UserStore](...)`).

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, StringValidator, Validator

@dataclass
class User:
    n: int = IntegerValidator(min_value=0)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    name: str = StringValidator(max_length=50, required=True, doc="Display name")
```

`rank` uses `Validator` because `in_choice` is a closed string list, not
a new store type. `n` uses `IntegerValidator` because the store is `int`.
`name` uses `doc=` so OpenAPI / your help text can read `User.__dict__["name"].doc`.

Specified path units bind at construct (`_active_units`): type always;
`min_value` / `pattern` / `reassign=False` / … only when that bound is
set. Mutating those kwargs after `__init__` does not rebuild the path —
pass them at construct. A subclass that replaces `validation_path`
keeps its declared units. An unknown validation-path unit raises
`ValueError`, not `KeyError`.

Runnable: [`examples/validator_kwargs.py`](../../examples/validator_kwargs.py).

## Constructor map

Every keyword `Validator(...)` accepts. Facades accept the same set
plus their extra (`region=`, `expire_*`, `path_exists=` — see
[typed](typed.md) / [named](named.md)).

| kwarg | omitted | meaning |
|---|---|---|
| `name` | from `__set_name__` | field name in error messages |
| `doc` | `None` | your help string on the descriptor |
| `default` | unset | used when assigned `None`; falsy `0`/`False`/`""` stay |
| `default_factory` | unset | zero-arg callable per None assignment; `not a Field twin` |
| `required` | `False` | `None` rejected when True |
| `debug` | `True` | re-raise; `False` swallows |
| `collect_all` | `True` | continue remaining concerns |
| `logger` | `False` | `True` → `module.qualname.field`. [logging](../how-to/logging.md) |
| `min_length` / `length` / `max_length` | unset | sized values; `length` is exact |
| `min_value` / `max_value` | unset | inclusive |
| `gt` / `lt` | unset | exclusive |
| `value` / `eq` | unset | exact; aliases of each other |
| `multiple_of` | unset | remainder; `0` accepts only `0` |
| `pattern` | unset | `PatternType` / compiled / str |
| `in_choice` / `not_in_choice` | unset | skip `None`; must be a `Container` at construct |
| `reassign` | `True` | `False` rejects a second set |
| `annotation` | from `Validator[T]` or owner | type door (class attr, not a typical call kwarg) |

`default=` and `default_factory=` together is `TypeError`.
`default_factory=` is a zero-arg callable invoked on each None
assignment (dataclass-shaped, still the descriptor — not a Field twin).

---

## `name`

Error messages start with the field name: `seats expect the minimum
value of 0`. You almost never pass this. `__set_name__` fills it from
the class body (`seats: int = IntegerValidator(...)`).

Pass `name=` only when the descriptor is **not** a class attribute
(a free-standing validator you call by hand) or when two names would
otherwise collide.

```python
from ux_valio import IntegerValidator

n = IntegerValidator(name="seats", min_value=0, debug=True)
n.__set__(object(), -1)  # ValueError: seats expect the minimum value of 0
```

A mismatch with the class attribute name TypeErrors at bind:
`IntegerValidator(name="age")` on a field called `n` is
`age != n, attribute names did not match`.

## `doc`

A `str` stored on the descriptor for **your** help, OpenAPI, or admin
UI. It is also the descriptor’s `__doc__`, so `help(Profile.bio)` shows
it. Read it as `Profile.__dict__["bio"].doc`.

```python
from dataclasses import dataclass
from ux_valio import StringValidator

@dataclass
class Profile:
    bio: str = StringValidator(max_length=160, doc="Public bio, 160 chars.")

assert Profile.__dict__["bio"].doc == "Public bio, 160 chars."
```

Non-str `doc=` is `TypeError` at construct. Omitted `doc` is `None`.
Compose: conflicting specified `doc` TypeErrors (same rule as `default`).

## `default`

Used when the assigned value is **`None`**. Not used for `0`, `False`,
or `""` — those are real values ([honesty](../explanation/honesty.md)).

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, Validator

@dataclass
class Seat:
    count: int = IntegerValidator(min_value=0, default=1)
    rank: str = Validator(in_choice=["A", "B"], default="A")

assert Seat().count == 1          # None → default
assert Seat(count=0).count == 0   # 0 is kept
assert Seat(rank=None).rank == "A"
```

`default=[]` is the **same list** on every instance (shared mutable).
Use `default_factory=list` for a new list each time.

A callable `default=` is still **invoked** (`default=list` already
built a new list). Prefer `default_factory=` when the intent is
per-instance.

## `default_factory`

Zero-arg callable, invoked on each `None` assignment. Same shape as
`dataclasses.field(default_factory=...)`, still the descriptor —
not a Field twin.

```python
from dataclasses import dataclass
from uuid import UUID, uuid4
from ux_valio import UUIDValidator

@dataclass
class Account:
    account_id: UUID = UUIDValidator(default_factory=uuid4)

a, b = Account(), Account()
assert a.account_id != b.account_id
```

`default=` and `default_factory=` together is `TypeError`.
A non-callable factory is `TypeError` at construct.

## `required`

`required=True` rejects **`None`**. It does **not** reject `""`. Empty
string is `min_length=1`. Both together is the usual “must type
something”:

```python
name: str = StringValidator(required=True, min_length=1)
```

`User(name=None)` → required. `User(name="")` → min_length.
Omitted `required` is optional (`None` may then hit `default`).

## `debug`

Omitted is `True`: failures raise. `debug=False` swallows, appends to
`Field.errors`, leaves the attribute unset (`read` is `None`).
[Honesty](../explanation/honesty.md). Do not overload `debug` into
collect-all.

## `collect_all`

Omitted is `True`: remaining concerns on **this field** still run.
One failure re-raises as itself; two or more are `ValidationErrors`.
`collect_all=False` is fail-fast (first concern wins). Per-field, not
per-dataclass — a later field is not reached once an earlier field
raises.

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, ValidationErrors

@dataclass
class Count:
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)

Count(n=3)    # ValueError (only multiple_of)
Count(n=-3)   # ValidationErrors (min_value and multiple_of)
```

## `logger`

OFF by default. `logger=True` binds `module.qualname.field`. Full
usage: [field-level logging](../how-to/logging.md).

## Length: `min_length`, `length`, `max_length`

These call `len(value)`. Unsized values (`int`) TypeError:
`expect a sized value`. `None` skips (use `required` for None).

| kwarg | meaning |
|---|---|
| `min_length=3` | `len(value) >= 3` |
| `max_length=20` | `len(value) <= 20` |
| `length=16` | exact; card PAN, OTP |

`max_length < min_length` is construct `ValueError`.
`length` below `min_length` or above `max_length` is construct
`ValueError`. Bound `0` is specified: `min_length=0` allows `""`.

```python
pin: str = StringValidator(length=4)           # exactly 4
tag: str = StringValidator(min_length=2, max_length=32)
```

## Value: `min_value`, `gt`, `value`/`eq`, `max_value`, `lt`

Comparisons use `<` / `>` on the stored type (ints, strings, dates).

| kwarg | meaning |
|---|---|
| `min_value=0` | `value >= 0` (inclusive). Bound `0` is specified. |
| `max_value=10` | `value <= 10` |
| `gt=0` | `value > 0` (exclusive). Cannot pair with `min_value`. |
| `lt=10` | `value < 10`. Cannot pair with `max_value`. |
| `value=5` or `eq=5` | exact. Aliases; both set is TypeError. |

`gt` and `min_value` together is construct error
(`select one`). Same for `lt`/`max_value` and `value`/`eq`.

```python
from ux_valio import IntegerValidator

seats = IntegerValidator(min_value=0, max_value=10)   # 0 and 10 ok
price = IntegerValidator(gt=0)                        # 0 rejected
locked = IntegerValidator(eq=2)                       # only 2
```

Strings compare lexicographically: `StringValidator(min_value="B")`
rejects `"Ace"`.

## `multiple_of`

Remainder: `value % multiple_of == 0`. `multiple_of=0` accepts **only**
`0`. `None` skips.

```python
n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)
# 0, 2, 4, 6, 8, 10 ok; 3 fails; -2 fails min_value
```

## `pattern`

A `PatternType` (`Digit(count=4)`), a compiled `re.Pattern`, or a `str`
regex. Match is **findall substring**, not fullmatch.
[Pattern](pattern.md).

```python
from ux_valio import Digit, StringValidator

otp: str = StringValidator(pattern=Digit(count=6), length=6)
```

## `in_choice` / `not_in_choice`

Closed set / ban-list. Must be a `Container` **at construct** (a
`list`, `tuple`, `set`, `str`, …). A non-container TypeErrors then,
not at assignment. `None` skips both (optional unset). A string used
as `in_choice` must not TypeError on that skip (characters are the
members — usually pass a list of strings instead).

```python
rank: str = Validator(
    in_choice=["Male", "Female", "Trans"],
    not_in_choice=["unknown"],
    default="Female",
)
```

## `reassign`

Omitted / `True`: the field may be set again. `reassign=False`: a
second `__set__` on the same instance raises `AttributeError`
(`attempted to reassign with value '…' instead`). Delete drops the
count, so you can set again after `del obj.field`.

```python
from dataclasses import dataclass
from ux_valio import StringValidator

@dataclass
class Once:
    token: str = StringValidator(reassign=False)

row = Once(token="abc")
row.token = "xyz"   # AttributeError: attempted to reassign

del row.token
row.token = "xyz"   # ok
```

Use this for write-once ids, not for “frozen dataclass”
(`@dataclass(frozen=True)` already blocks assign).

## `annotation` (type door)

Not usually passed to `__init__`. `Validator[int]` and typed facades
fill it. Bind: `is_subclass_of(owner, validator)`. Set:
`is_instance_of(value, annotation)`. Optional needs `| None` on
**both** sides. See [typing](../how-to/typing.md).

---

## Leaves

Min/max length and value leaves (`MinLengthValidator`,
`MaxLengthValidator`, `MinValueValidator`, `MaxValueValidator`) are
public building blocks, with `TypeValidator`, `RequiredValidator`,
`PatternValidator`, `ChoiceValidator`, `ReassignValidator`,
`MultipleValidator`, `ValueValidator`. `AttributeValidator` is **not**
shipped. Check object attributes at the call site or with `validator`.

List / dictionary / set / tuple collection facades are not
shipped; `list[T]` / `dict[K, V]` membership is the type check.

Use a leaf when you want **one** concern as the descriptor
(`tag: str = LengthValidator(min_length=3) & RequiredValidator(required=True)`).
Day-to-day, pass the same kwargs on `StringValidator` / `Validator`.

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

## Facade-only kwargs

Not on `Validator.__init__`. Wrong names TypeError as unknown.

| facade | extra | page |
|---|---|---|
| `PhoneNumberValidator` | `region="IN"` (required) | [named](named.md) |
| `ExpiryValidator` | exactly one of `expire_before` / `expire_on` / `expire_after` | [named](named.md) |
| `PathValidator` | `path_exists=True` | [typed](typed.md) |

Hang methods (`pre_validate`, `task_*`, …) are not constructor kwargs.
They are decorators on the field: [Hang API](../how-to/hang.md).
