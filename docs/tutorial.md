# Tutorial

This page is the whole first hour. After it you can put a validator on a
dataclass field, hang a uniqueness check, and know where the rest of the
handbook lives.

Python ≥ 3.14. Install the library in the project:

```console
pip install -e .
pip install ux-valio[phonenumbers]   # only if you need PhoneNumberValidator
```

## What you are installing

ux-valio is a **descriptor**. You put it on the right-hand side of a
field. When someone assigns that field, the descriptor type-checks,
applies bounds, runs any functions you hung on the name, and stores the
value on the instance. It is not a BaseModel. It does not wrap your
class. Your class stays a dataclass (or a plain class, or a TypedDict).

Pydantic writes `name: str = Field(max_length=50)` — two objects, a type
and a Field twin. Here the validator **is** the field default:

```python
name: str = StringValidator(max_length=50)
```

There is no Field twin and no Schema twin. Do not use bare `Property` as
the field default — it is the descriptor base, not a product facade.

## A first form

A signup field needs a string that is present and not longer than 50
characters. `StringValidator` stores `str`. `required=True` means
`None` is rejected. `max_length=50` is inclusive.

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, StringValidator, Validator

@dataclass
class User:
    name: str = StringValidator(max_length=50, required=True)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)

ada = User(name="Ada", n=4)
assert ada.name == "Ada"
User(name="x" * 51)  # ValueError: too long
```

What each field is doing:

| field | what it stores | when you would use it |
|---|---|---|
| `name` | `str` | any free text with a length cap (display name, title) |
| `rank` | `str` from a closed list | gender, role, status — `in_choice` is the enum-without-Enum |
| `n` | `int` | seats, quantity, age — `multiple_of=2` is “even numbers only” |

`User(name="Ada")` is enough for `rank`: omitted `None` is replaced by
the `default`. `n` has no default, so you must pass it.

Three traps that look like bugs and are not:

- `required=True` rejects **`None`**. An empty string `""` is still a
  string. To reject blanks, add `min_length=1`.
- Assigned `0` / `False` / `""` are **not** replaced by `default`. Only
  `None` is. A seat count of `0` is a real value.
- You do not pass `debug=True` on every field. Omitted `debug` is
  already `True` (failures raise). Omitted `collect_all` is `True`
  (several concerns on one field surface together). Omitted `logger` is
  OFF (no log files). To watch one field, see
  [field-level logging](how-to/logging.md).

## Hang a rule the validator does not already own

Length and “required” are kwargs. “Must not be `admin`”, “must not
already be in the database”, “strip then casefold” are **your** rules.
You hang them on the field name, in the same class body.

```python
@dataclass
class Handle:
    handle: str = StringValidator(min_length=3, required=True)

    @handle.pre_validate
    def fold(self, value: str) -> str:
        return value.strip().casefold()

    @handle.post_validate
    def not_reserved(self, value: str) -> str:
        if value in {"admin", "root"}:
            raise ValueError("reserved handle")
        return value
```

`Handle(handle="  Ada  ")` stores `"ada"`. `Handle(handle="Admin")`
raises after fold, because the reserved check sees the folded value.

**Where each hang belongs:**

1. `pre_validate` — change the value (strip, casefold, compact spaces).
   **Return** the value you want stored. Forgetting the return stores
   `None`.
2. Built-in `validate()` — identity you already declared (`required`,
   `min_length`, checksum on a named facade). You do not hang this.
3. `post_validate` — policy that needs a valid value (reserved names,
   “is this username taken?”). Invalid input never hits the database.
4. `post_set` — persist / reserve after the value is on the instance.

The full table, including background `task_*` and get/delete, is
[Hang API](how-to/hang.md). A complete register+login form is
`examples/signup.py`.

## Several independent rules on one field

A password must be long **and** contain a digit **and** contain a
letter. Those are three separate “does this string contain X?” checks.
Pattern `&` **concatenates** (it builds one regex: “this, then that”).
Independent findalls belong under `AllOf`:

```python
from ux_valio import AllOf, Digit, Pattern, SetOf, StringValidator

password: str = AllOf(
    StringValidator(required=True, min_length=8),
    StringValidator(pattern=Digit(count_min=1)),
    StringValidator(pattern=SetOf(Pattern(r"A-Za-z"), count_min=1)),
)
```

`AllOf` is AND. `|` is OR
(`IntegerValidator | StringValidator` accepts either). Walkthrough:
[compose](how-to/compose.md).

## An identity that already has a checksum

GSTIN, IBAN, Aadhaar, payment cards are not `StringValidator(min_length=…)`.
They are named facades: print grouping is stripped, the stored value is
the compact identity, and the checksum runs as part of `validate()`.

```python
from ux_valio import GSTINValidator, IBANValidator

gstin: str = GSTINValidator()
iban: str = IBANValidator()
```

`Counterparty(gstin="09 AAAPA1111F 1Z P")` stores `"09AAAPA1111F1ZP"`.
A checksum mismatch raises `ValueError`. When to pick which identity:
[named identities](reference/named.md). Copy-paste vendor onboarding:
`examples/vendor.py`.

## A store, hasher, or gateway (a port)

Uniqueness needs a database. The form should not construct a SQL client
inside the hang. Inject a port as a dataclass field **above** the
product fields (declaration order is `__init__` order):

```python
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from ux_valio import StringValidator, Validator

@runtime_checkable
class UserStore(Protocol):
    def username_taken(self, username: str) -> bool: ...

@dataclass
class Register:
    users: UserStore = field(
        default=Validator[UserStore](required=True),
        repr=False,
        compare=False,
    )
    username: str = StringValidator(required=True, min_length=3)

    @username.post_validate
    def available(self, value: str) -> str:
        if self.users.username_taken(value):
            raise ValueError("taken")
        return value
```

`@runtime_checkable` is required so `Validator[UserStore]` can
`isinstance` the fake and the SQL adapter. `InitVar` is too late —
uniqueness runs before `__post_init__`. Why, and the full skeleton:
[workflows](how-to/workflows.md), [choices](explanation/choices.md).

## Typing

The annotation on the left is the **store type** (`str`, `int`), not the
validator class. Runtime the instance sees `str`. Construction is `Any`
to type checkers (`ValidateProperty.__new__`; mypy via
`plugins = ["ux_valio.mypy_plugin"]`) so `StringValidator()` assigns to
`str`. No per-type mixin. `User(name=1)` still errors at runtime.

`Validator[int]` is the same descriptor with the stored type on it.
Use it on a plain class (no field annotation) or next to `n: int` — the
two must agree. `IntegerValidator` is already `Validator[int]`.

```python
class Stats:
    n = Validator[int](min_value=0)
```

An unconstrained `TypeVar` (`item: T = Validator()` on a generic class)
is typing-only; runtime cannot specialize one descriptor per `Box[int]`
/ `Box[str]`. Details: [typing](how-to/typing.md).

## Where to go next

| I need to… | Page |
|---|---|
| Hang uniqueness / persist / email | [Hang hooks](how-to/hang.md) |
| Combine rules / OR two types | [Compose](how-to/compose.md) |
| Validate a JSON dict | [TypedDict schema](how-to/typed-dict.md) |
| Copy a production workflow | [Workflows](how-to/workflows.md) · [`examples/`](../examples/) |
| Look up a kwarg | [Validator](reference/validator.md) |
| Understand a KEEP default | [Choices](explanation/choices.md) · [Honesty](explanation/honesty.md) |
