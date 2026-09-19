# TypedDict schema

Use a TypedDict when the payload is a **dict** (JSON body, query string,
msgpack) and you do not want a dataclass instance. Pydantic would ask
you to subclass `BaseModel`. Here the TypedDict **is** the schema
(stdlib, no BaseModel). Extra keys fail-closed. `total=False` and
PEP 655 `Required` / `NotRequired` are the TypedDict metaclass
(`__required_keys__`) — hang extras with `Annotated`, or the same
assignment as a dataclass (`name: str = StringValidator()`), then
`@name.pre_validate` / `@name.validator` in the TypedDict body. `self`
in those hooks is the mapping. No Schema twin.

**Where this shows up:** an invite API, a webhook, a settings blob you
round-trip as JSON. Nested TypedDict values recurse. Copy-paste:
`examples/invite.py`.

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

`Signup(person={"name": "  Ada  ", "email": "ada@example.com", "age": 36})`
stores `{"name": "Ada", "email": "ada@example.com", "age": 36}`.
A leftover key `"admin": True` raises. `age` has no extra hang: it is
checked as `int` by the type door.

`min_length=2` already rejects `""`. The hang is a name policy (no
digits), not a second blank check. Production uniqueness hangs on a
store port — see `examples/invite.py`.

Two ways to attach a validator to a key, same effect:

- `name: str = StringValidator(min_length=2)` — dataclass-shaped, and
  you can hang `@name.pre_validate` because `name` is that descriptor.
- `email: Annotated[str, EmailValidator()]` — PEP 593, useful when you
  do not need a hang on that key.

Omitted `NotRequired` keys skip extras. `ReadOnly` peels like the other
qualifiers. Nested TypedDict values recurse.

If the payload should be an object with ports and `post_set` persist,
use a dataclass ([workflows](workflows.md)), not a TypedDict. TypedDict
has no generated `__init__` field order for injecting a store — wrap it
in a dataclass field (`person: Person = Validator()`) and put the port
on that outer class, as `examples/invite.py` does.
