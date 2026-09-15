# ux-valio

Door A descriptor-on-dataclass validation. Greenfield reimplementation of
[`bitplorer/valio`](https://github.com/bitplorer/valio) frozen at
[`3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
Valio itself is not edited.

## Install

```console
pip install -e .
```

## Door A

The public caller shape is a validator as the dataclass field default:

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, LengthValidator, RequiredValidator, StringValidator, Validator

@dataclass
class User:
    name: str = StringValidator(debug=True, max_length=50, required=True)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2, debug=True)
    tag: str = LengthValidator(min_length=3, debug=True) & RequiredValidator(required=True)
```

There is no Field twin and no Schema twin. `field: T = SomeValidator(...)` is
the door.

Concern leaves (`LengthValidator`, `RequiredValidator`, …) and facades compose
with `&` (AllOf) / `|` (AnyOf), or explicit `AllOf` / `AnyOf` / `Chain`, as
**one** descriptor. Facades do not multiple-inherit leaves.

## KEEP: debug swallow, logger OFF, pre_set hook

- `debug=True` re-raises on a failed set/get/delete.
- `debug` falsy (including the default `None`) swallows the exception, appends
  it to `errors`, and leaves the attribute unset so later reads are `None`.
  This swallow is KEEP. The product does not fail-closed-by-default.
- `logger` defaults **OFF** (`False`). Valio's `logger=None` enabled file
  logging; ux-valio does not.

**Only the descriptor `pre_set` hook return is stored.** That hook *is*
`pre_validate → validate → post_validate`. There is no `_processors["pre_set"]`
bag and no `add_pre_set` — hang before-store work on `add_pre_validator`
(transform; **return the value**), `add_validator` (check; return ignored),
or `add_pre_validator_task` (side effect; return ignored). `add_post_set`
runs after store; its return is ignored.

`add_*` / `add_*_task` accept **sync or async** callables. `async def`
registers. Coroutine **objects** at run are not a second reject door: same
run rules as `async def`.

**Run rules:** on the sync descriptor path,
- no running loop → `TypeError` (`async callable needs a running event loop / helper`).
  Not silent `None`, not `asyncio.run`.
- running loop → nest-safe sync-bridge (private loop in a worker thread).
  Assign from an async context (`asyncio.run` of a small harness or
  pytest-asyncio). Same-thread `run_until_complete` on the caller's loop
  is a nested-loop hazard.

`asyncio.run` is not used in `__set__`.

### Before-store DB check (Register)

valio README taught this on Door B (`@user_field.add_pre_valiator` — typo
for `add_pre_validator`). Door A hangs the same processor on the descriptor.
Do **not** invent `add_pre_set`. A uniqueness **task** is the wrong bag
(valio `cache_task=True` skipped re-checks).

Class-body `username: str = username` is `NameError` (the assignment makes
`username` local). Match valio Field’s `user_field` / `user` split:

```python
from dataclasses import dataclass
from ux_valio import StringValidator

DB = {"taken"}
username_field = StringValidator(debug=True, required=True, min_length=3)

@dataclass
class Register:
    username: str = username_field

    @username_field.add_pre_validator
    def username_not_taken(self, value: str) -> str:
        if value in DB:
            raise ValueError("username already registered")
        return value
```

Module-level `@username_field.add_pre_validator` without `namespace="Register"`
does not fire (bag key is the function name). A **module-level** method
decorator’s `__qualname__` is `Register.fn`, which matches. A method on a
class defined inside a function (`test_fn.<locals>.Register.fn`) keys as
`test_fn` and silently does not fire — pass `namespace="Register"`.

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
Bound `0` is specified: `min_value`/`max_value` inclusive, `gt`/`lt`
exclusive, `multiple_of` is remainder, `multiple_of=0` accepts only `0`.

`PatternValidator` matches with `re.findall` (substring), not `fullmatch`.

## Typed facades

`IntegerValidator`, `StringValidator`, `BooleanValidator`, `FloatValidator`,
`DecimalValidator`, `BytesValidator`, `DateValidator` (`datetime.date`),
`EmailValidator`, `UUIDValidator` (coerces UUID strings), `PathValidator`
(coerces `str` → `pathlib.Path`; `path_exists=True` requires the path to
exist), `IPv4Validator` / `IPv6Validator` / `IPAddressValidator`, and
`EnumValidator` / `IntegerEnumValidator` / `StringEnumValidator`.

Min/max length and value leaves (`MinLengthValidator`, `MaxLengthValidator`,
`MinValueValidator`, `MaxValueValidator`) are public building blocks.

`AttributeValidator` is **not** shipped. Check object attributes at the call
site or with `add_validator`. Payment-card, named-once, and expiry leaves
are out of scope. RGB/HSL color validators are retired.

## Migration (Door B → Door A)

Valio README taught a second door: construct a `*Field`, hang decorators on
it, then assign `password: str = password_field.validator`. That Field factory
duplicated kwargs, dropped `gt`/`lt`/`eq`/`multiple_of`/`in_choice` from its
signature, and is untested. ux-valio retires Door B. Move the kwargs onto
`StringValidator` / `IntegerValidator` / `Validator` as the dataclass default,
and hang `add_pre_validator` / `add_validator` on that descriptor. Star-import
of valio's 306 names is gone; import the names in `__all__`.

## Public surface

`Validator`, typed facades, concern leaves, `AllOf` / `AnyOf` / `Chain`, and
`Pattern` / `PatternType` combinators (`&` / `|`). Concern leaves also compose
as validator objects (`LengthValidator(...) & RequiredValidator(...)`).
No multiple inheritance of leaves, no Cap Host, no `rule/`.
