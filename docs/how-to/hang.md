# Hang hooks

Hang `pre_validate` / `validator` / `post_set` / `task_*` on the field
name. The descriptor *is* the dataclass default — no outer
`username_field` twin, no Field mixin. Those methods live on
`ValidateProperty` (leaf or facade). Do not invent `pre_set` as a hang —
`_run_pre_set` *is* the validate pipeline.

## Hang API

Process is the default kind (pipeline must finish). `task_*` is
background (setter does not wait). `validator` is a check during
`validate()` (attrs `@x.validator`; return ignored). Sync or async.

| hang | when | return |
|---|---|---|
| `pre_validate` | before validate | **stored** |
| `post_validate` | after validate | **stored** |
| `validator` | during `validate()` | ignored |
| `post_set` | after store | ignored |
| `pre_get` / `post_get` | around read | ignored (sees the field **name**) |
| `pre_delete` / `post_delete` | around delete | ignored (sees the field **name**) |
| `task_pre_validate` … `task_post_delete` | same phases, background | ignored |
| `wait_tasks` | tests / shutdown | — |

No hang named `pre_set`. Persist/reserve that must fail-closed hangs on
`post_set`. Welcome-email hangs on `task_post_set`.
`from ux_valio import wait_tasks`.

**Only the before-store pipeline return is stored.** That pipeline *is*
`pre_validate → validate → post_validate`.

- `pre_validate` — transform (`strip`, `casefold`); **return the value**
- `validate()` — identity (`required`, `min_length`, checksum, …)
- `post_validate` — store lookup (uniqueness) **after** identity; invalid
  names never hit the database
- `post_set` — persist / reserve (fail-closed)

```python
from dataclasses import dataclass, field
from ux_valio import StringValidator

@dataclass
class Register:
    users: UserStore = field(repr=False, compare=False)
    username: str = StringValidator(required=True, min_length=3)

    @username.pre_validate
    def fold(self, value: str) -> str:
        return value.strip().casefold()

    @username.post_validate
    def username_not_taken(self, value: str) -> str:
        if self.users.username_taken(value):
            raise ValueError("username already registered")
        return value

    @username.post_set
    def commit(self, value: str) -> None:
        self.users.commit(value)
```

`users` is the injected store (one shared instance from the service),
not a product column. `required` / `min_length` already reject `None`
and short strings — do not hang `if not value`. See
`examples/registration.py`.

Class access `User.name` is that descriptor, so `User.name.post_set`
also works after the class exists. A shared descriptor (`aadhaar` on
Person and Vendor) uses the class you accessed:
`Person.aadhaar.pre_validate` registers under Person, not the last
`__set_name__`.

Processor and task registries use the owning class’s `module.qualname`.
Two classes named `User` in different modules do not share hooks.
Lookup walks the instance MRO (base first), so a child runs parent
field hooks. A free function on an **unbound** descriptor needs
`namespace=` (the owning class, or its `module.qualname` str).
`namespace="Register"` is not rewritten to match lookup. A processor
that forgets to return the value stores `None`.

## Sync and async

`pre_validate` / `task_*` accept **sync or async** callables. `async def`
registers. On the sync descriptor path:

- no running loop → `TypeError` (`async callable needs a running event loop / helper`)
- running loop → nest-safe sync-bridge (process-held worker)
- re-entering that worker is `TypeError` (would deadlock), not a hang

`asyncio.run` is not used in `__set__`. `from ux_valio import wait_tasks`
waits for tasks (tests / shutdown).
