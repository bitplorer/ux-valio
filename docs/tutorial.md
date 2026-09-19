# Tutorial

Python ≥ 3.14.

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

Next: [hang hooks](how-to/hang.md), [named identities](reference/named.md).
