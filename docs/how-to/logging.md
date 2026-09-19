# Field-level logging

Every validator is one field. `logger=` is **that field’s** log, not a
package-wide logger and not a `logs/` directory. Pydantic has no
equivalent: you either log the whole model or nothing. Here you can
watch `Ticket.seats` without hearing `Ticket.note`.

**Where:** a form you are debugging, an audit trail on one sensitive
column, a staging deploy where you need to see which field rejected
input. Leave it **off** on a hot path ([performance](../explanation/performance.md)).

Runnable file: [`examples/field_logging.py`](../../examples/field_logging.py).

## What it is

| you pass | what happens |
|---|---|
| omitted / `logger=False` | OFF (default). No records. |
| `logger=None` | OFF. Not valio’s None=on. |
| `logger=True` | at `__set_name__`, binds a stdlib logger named `module.qualname.field` |
| `logger=<logging.Logger>` | that object is used as-is (add your own `FileHandler` if you want a file) |

ux-valio never opens a file and never creates `logs/`. If you need a
file, configure **your** logger.

After bind, `Ticket.__dict__["seats"].logger` is a `logging.Logger`,
not the bool `True`. Specified-theory (`_opts.logger`) still records
that you passed `True`, so compose can detect `logger=True` vs
`logger=False` conflicts.

## What gets logged

| event | level | message shape |
|---|---|---|
| successful `__set__` | `INFO` | `Ticket.seats: set` |
| successful `__get__` | `INFO` | `Ticket.seats: get` |
| successful `__delete__` | `INFO` | `Ticket.seats: delete` |
| validation failure | `ERROR` | the exception string (`seats expect a maximum value of 10, got 12 instead`) |

The value itself is **not** in the message. Usernames, card numbers, and
Aadhaar do not leak into logs. If you need the value, hang `post_set`
and log it yourself under a policy you control.

## `logger=True` — one field, stdlib name

```python
import logging
from dataclasses import dataclass
from ux_valio import IntegerValidator, StringValidator

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")

@dataclass
class Ticket:
    holder: str = StringValidator(required=True, min_length=2, logger=True)
    seats: int = IntegerValidator(min_value=0, max_value=10, logger=True)
    note: str = StringValidator(default="")  # omitted logger stays OFF
```

After the class body:

```text
Ticket.__dict__["holder"].logger.name
# "your_module.Ticket.holder"
```

`Ticket(holder="Ada", seats=2)` emits:

```text
your_module.Ticket.holder INFO Ticket.holder: set
your_module.Ticket.seats  INFO Ticket.seats: set
```

`Ticket(holder="Ada", seats=99)` also emits an ERROR on `seats` and
raises `ValueError` (`debug` omitted is True). `note` is silent.

Listen to **one** field:

```python
logging.getLogger("your_module.Ticket.seats").setLevel(logging.ERROR)
# seats: failures only. holder: still INFO if its logger is INFO.
```

## Your own `logging.Logger`

Use this when the name must be stable (`boxoffice.audit`) or when you
want a `FileHandler` / `SysLogHandler` the library will not add.

```python
import logging
from ux_valio import StringValidator

audit = logging.getLogger("boxoffice.audit")
audit.setLevel(logging.INFO)
audit.addHandler(logging.StreamHandler())   # or FileHandler in *your* app

reason: str = StringValidator(min_length=3, logger=audit)
```

The descriptor keeps that object. `logger=True` is not mixed in.

## Compose

Members that **specify** different logger values TypeError at class
body:

```python
from ux_valio import LengthValidator, RequiredValidator

LengthValidator(min_length=1, logger=True) & RequiredValidator(
    required=True, logger=False
)  # TypeError: conflicting logger
```

An **omitted** logger on one member still collapses to the other’s
explicit `True`. Pass `logger=` once on the compose root if both should
log:

```python
from ux_valio import AllOf, StringValidator

tag = AllOf(
    StringValidator(min_length=3),
    StringValidator(required=True),
    logger=True,
)
```

## `debug=False` + logger

Swallow (`debug=False`) still **records** the ERROR, then leaves the
attribute unset. You get a log line and `field.errors` without a raise.
That is how you watch a batch import without aborting the row.

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator

@dataclass
class Row:
    n: int = IntegerValidator(min_value=0, debug=False, logger=True)

row = Row(n=-1)
assert row.n is None
# ERROR logged; Row.__dict__["n"].errors holds the ValueError
```

## What not to do

- Do not expect a file named `User.name.log`. There is none.
- Do not pass `logger="User.name"` (a str). Bool or `logging.Logger`.
- Do not turn `logger=True` on every facade in production — each get
  is an INFO call ([performance](../explanation/performance.md)).
- Do not hang a `print` in `pre_validate` “for logging”. That bypasses
  levels, names, and the no-value-in-message contract.

Contract remainder: [Honesty](../explanation/honesty.md).
