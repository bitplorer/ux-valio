# Hang hooks

A hang is a method you attach to **one field**, in the class body, with
the field’s descriptor as the decorator. You use it when a kwarg cannot
express the rule: strip, reserved names, “is this username taken?”,
“write the row”, “send welcome email”.

The descriptor *is* the dataclass default — no outer `username_field`
twin, no Field mixin. Those methods live on `ValidateProperty` (leaf or
facade). Do not invent `pre_set` as a hang — `_run_pre_set` *is* the
validate pipeline.

You hang in a **dataclass**, a **plain class**, or a **TypedDict** body.
`self` is the instance (or the mapping, on TypedDict). You do **not**
hang on a function, a Pydantic model, or a Field object — there is no
Field object.

## Hang API

Process is the default kind (pipeline must finish). `task_*` is
background (setter does not wait). `validator` is a check during
`validate()` (attrs `@x.validator`; return ignored). Sync or async.

| hang | when you use it | return |
|---|---|---|
| `pre_validate` | transform before identity (strip, casefold, compact spaces) | **stored** |
| `post_validate` | uniqueness / policy **after** identity (DB lookup, reserved set) | **stored** |
| `validator` | extra check during `validate()`, attrs-shaped; cannot transform | ignored |
| `post_set` | persist / reserve after the value is on the instance | ignored |
| `pre_get` / `post_get` | audit or lazy side-effect around read | ignored (sees the field **name**) |
| `pre_delete` / `post_delete` | audit around delete | ignored (sees the field **name**) |
| `task_pre_validate` … `task_post_delete` | same phases, but background (email, metrics) | ignored |
| `wait_tasks` | tests / shutdown — wait for spawned tasks | — |

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

A processor that forgets to return the value stores `None`. `validator`
is a check (attrs-shaped); its return is ignored on purpose so you do
not think it can transform. Transform is `pre_validate` /
`post_validate` only.

### `pre_validate` — change the value

Use this for anything that should happen **before** length/checksum, so
`"  Ada  "` becomes `"ada"` and then `min_length` sees `"ada"`. Always
`return` the new value.

### `post_validate` — talk to a store

Use this for “is this GSTIN already on file?” Identity has already
passed, so you do not spend a query on `"ab"`. Return the value (or a
canonical form from the store). Raise `ValueError` on conflict.

### `post_set` — write after store

The value is already on `self`. Use this to INSERT / reserve stock /
authorize a card hold. Hang it on the **last** product field if several
fields must all succeed first (signup persists on `account_id`, checkout
reserves on `quantity`). If this raises, the assignment fails — that is
the fail-closed persist.

### `task_post_set` — do not block the setter

Welcome email, analytics, cache bust. The setter does **not** wait. A
failed email must not roll back the user row — that is why it is not
`post_set`. In tests, `wait_tasks()` after the assignment.

### `validator` — attrs-shaped check

Same moment as the built-in path (`validate()`), return ignored. Use it
when you want a named check next to kwargs (“no digits in the handle”)
and you are not transforming. If you need to transform, use
`pre_validate`.

## A register field, end to end

```python
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from ux_valio import StringValidator, Validator

@dataclass
class Register:
    users: UserStore = field(
        default=Validator[UserStore](required=True),
        repr=False,
        compare=False,
    )
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

`users` is a dataclass field so generated `__init__` assigns it **before**
`username` (declaration order). `Validator[UserStore]` type-checks the
port (`@runtime_checkable` Protocol). `repr=False, compare=False` keeps
it out of `repr` / `eq` — injected store, not a product column.
`InitVar` + `__post_init__` is too late. See `examples/signup.py`.

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

## Why this order exists

Identity before I/O. A name that fails `min_length` must not query the
users table. Persist after store so a failed later field does not
consume the name — hang `post_set` on the **last** product field, or
accept that an earlier field’s persist already ran. Tasks never decide
the write: the setter does not wait for them.

## Sync and async

`pre_validate` / `task_*` accept **sync or async** callables. `async def`
registers. On the sync descriptor path:

- no running loop → `TypeError` (`async callable needs a running event loop / helper`)
- running loop → nest-safe sync-bridge (process-held worker)
- re-entering that worker is `TypeError` (would deadlock), not a hang

`asyncio.run` is not used in `__set__`. `from ux_valio import wait_tasks`
waits for tasks (tests / shutdown). `enable_async` and `cache_task` are
not doors (unknown-kwarg TypeError).

If your service is already async, hang `async def` and assign from
async code that has a running loop. If your service is sync, hang
`def`. Mixing an `async def` hang into a sync `__init__` without a loop
is the TypeError above — that is intentional, not a missing helper.
