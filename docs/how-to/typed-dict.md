# TypedDict schema

A `TypedDict` is the schema (stdlib, no BaseModel). Extra keys
fail-closed. `total=False` and PEP 655 `Required` / `NotRequired` are
the TypedDict metaclass (`__required_keys__`) — hang extras with
`Annotated`, or the same assignment as a dataclass
(`name: str = StringValidator()`), then `@name.pre_validate` /
`@name.validator` in the TypedDict body. `self` in those hooks is the
mapping. No Schema twin.

```python
from dataclasses import dataclass
from typing import Annotated, TypedDict
from ux_valio import EmailValidator, StringValidator, Validator

class Person(TypedDict):
    name: str = StringValidator(min_length=2)
    email: Annotated[str, EmailValidator()]
    age: int

    @name.pre_validate
    def strip_name(self, value):
        return value.strip()

    @name.validator
    def no_digit(self, value):
        if any(char.isdigit() for char in value):
            raise ValueError("digits")

@dataclass
class Signup:
    person: Person = Validator()
```

`min_length=2` already rejects `""`. The hang is a name policy (no
digits), not a second blank check. Production uniqueness hangs on a
store port — see `examples/typed_dict_schema.py`.

Omitted `NotRequired` keys skip extras. `ReadOnly` peels like the other
qualifiers. Nested TypedDict values recurse.
