# Tutorial

Python ≥ 3.14. `pip install -e .` (phone extra:
`pip install ux-valio[phonenumbers]`).

## 1. The field default is the validator

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
User(name="x" * 51)  # ValueError
```

`required=True` rejects `None`. `min_length=1` rejects `""`. Assigned
`0` / `False` / `""` are not replaced by `default`. `None` is.

Omitted `debug` / `collect_all` are True. Omitted `logger` is OFF.

## 2. Hang on the field name

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

`pre_validate` returns the stored value. `post_validate` is uniqueness
/ policy after identity. Persist is `post_set`. Full table:
[Hang API](how-to/hang.md).

## 3. Compose concerns

```python
from ux_valio import AllOf, Digit, Pattern, SetOf, StringValidator

password: str = AllOf(
    StringValidator(required=True, min_length=8),
    StringValidator(pattern=Digit(count_min=1)),
    StringValidator(pattern=SetOf(Pattern(r"A-Za-z"), count_min=1)),
)
```

Pattern `&` concatenates. Independent findalls are `AllOf`. `Chain` is
`AllOf`. `|` is OR. See [compose](how-to/compose.md).

## 4. Named identity

```python
from ux_valio import GSTINValidator, IBANValidator

gstin: str = GSTINValidator()
iban: str = IBANValidator()
```

Stored value is the compact identity (grouping strips). Catalog:
[named identities](reference/named.md).

## 5. A port (store, hasher, gateway)

Declaration order: port first, then product fields. See
[workflows](how-to/workflows.md) and `examples/signup.py`.

## Typing

`Validator[int]` is the same descriptor with the stored type on it.
Use it on a plain class (no field annotation) or next to `n: int` — the
two must agree. `IntegerValidator` is already `Validator[int]`.

```python
class Stats:
    n = Validator[int](min_value=0)
```

An unconstrained `TypeVar` (`item: T = Validator()` on a generic class)
is typing-only; runtime cannot specialize one descriptor per `Box[int]`
/ `Box[str]`.

Runtime the instance sees `str`. Construction is `Any` to type checkers
(`ValidateProperty.__new__`; mypy via `plugins = ["ux_valio.mypy_plugin"]`)
so `StringValidator()` assigns to `str`. No per-type mixin.
`User(name=1)` still errors.

Next: [hang hooks](how-to/hang.md), [named identities](reference/named.md),
[choices](explanation/choices.md).
