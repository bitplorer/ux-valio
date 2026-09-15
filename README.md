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
with `&` (AllOf) / `|` (AnyOf), or explicit `AllOf` / `AnyOf`, as **one**
descriptor. `Chain` is `AllOf`. Facades do not multiple-inherit leaves.

Hang `add_*` on the descriptor that is the field default: a `Validator`
facade, or the compose **root** after `&` / `AllOf`. Concern leaves do not
carry `add_*`. Do not invent `add_pre_set`.

```python
name_field = StringValidator(debug=True, max_length=50) & RequiredValidator(required=True)

@dataclass
class User:
    name: str = name_field

    @name_field.add_pre_validator
    def strip(self, value: str) -> str:
        return value.strip()
```

## KEEP: debug swallow, logger OFF, pre_set hook

- `debug=True` re-raises on a failed set/get/delete.
- `debug` falsy (including the default `None`) swallows the exception, appends
  it to `errors`, and leaves the attribute unset so later reads are `None`.
  This swallow is KEEP. The product does not fail-closed-by-default.
- `collect_all=False` by default (fail-fast). `collect_all=True` continues
  remaining concerns and surfaces every failure as `ValidationErrors` (when
  `debug=True`) or as multiple entries on `errors` (when `debug` is falsy).
  Do not overload `debug` into collect-all.

  ```python
  n: int = IntegerValidator(
      min_value=0, max_value=10, multiple_of=2, collect_all=True, debug=True
  )
  ```
- Composing members that specify different `debug` or `default` values raises
  `TypeError`. A right-hand `debug=True` is not discarded into swallow.
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
`test_fn` and silently does not fire — pass `namespace="Register"`. That
silent miss is leftover teaching, not a second door. A processor that
forgets to return the value stores `None`; return the value from
`add_pre_validator`.

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
Bound `0` is specified: `min_value`/`max_value` inclusive, `gt`/`lt`
exclusive, `multiple_of` is remainder, `multiple_of=0` accepts only `0`.

`PatternValidator` matches with `re.findall` (substring), not `fullmatch`.

## Typed facades

`IntegerValidator`, `StringValidator`, `BooleanValidator`, `FloatValidator`,
`DecimalValidator`, `BytesValidator`, `DateValidator` (`datetime.date`;
strings are not parsed), `EmailValidator`, `UUIDValidator` (coerces UUID
strings), `PathValidator` (annotation `pathlib.Path`; coerces `str` →
`pathlib.Path`; `path_exists=True` requires the path to exist),
`IPv4Validator` / `IPv6Validator` / `IPAddressValidator`,
`EnumValidator` / `IntegerEnumValidator` / `StringEnumValidator`,
`PaymentCardValidator` (Visa / Mastercard / Amex / Discover / Rupay, each
Luhn **and** brand; a Luhn-valid non-brand number is rejected), and
`ExpiryValidator` (`expire_after` / `expire_on` / `expire_before` are
exclusive; a bad `expire_before` string is checked on that kwarg, not on
`expire_after`). `expire_*` are not accepted on `Validator`. There is no
`expiry` path unit — the check lives on the facade.

Named typed facades (`PathValidator`, IP, `PaymentCardValidator`,
`ExpiryValidator`) run their extra check from `validate()` after the
inherited path. They do not register that check with `add_validator` on
each assignment.

```python
from dataclasses import dataclass
from ux_valio import ExpiryValidator, PaymentCardValidator

@dataclass
class Card:
    number: str = PaymentCardValidator(debug=True)
    # expire_before is its own bound; do not also pass expire_after.
    until: str = ExpiryValidator(expire_before="2020-01-01", debug=True)
```

Phone, list/dict/set/tuple collection facades are not shipped.

Min/max length and value leaves (`MinLengthValidator`, `MaxLengthValidator`,
`MinValueValidator`, `MaxValueValidator`) are public building blocks.

`AttributeValidator` is **not** shipped. Check object attributes at the call
site or with `add_validator`. RGB/HSL color validators are retired.
`HexColorValidator` is not a public facade.

## Migration (Door B → Door A)

Valio README taught a second door: construct a `*Field`, hang decorators on
it, then assign `password: str = password_field.validator`. That Field factory
duplicated kwargs, dropped `gt`/`lt`/`eq`/`multiple_of`/`in_choice` from its
signature, and is untested. ux-valio retires Door B. Move the kwargs onto
`StringValidator` / `IntegerValidator` / `Validator` as the dataclass default,
and hang `add_pre_validator` / `add_validator` on that descriptor. Star-import
of valio's 306 names is gone; import the names in `__all__`.

## Public surface

`Validator`, typed facades, concern leaves, `AllOf` / `AnyOf` (`Chain` is
`AllOf`), `ValidationErrors`, and `Pattern` / `PatternType` combinators
(`&` / `|`). Concern leaves also compose as validator objects
(`LengthValidator(...) & RequiredValidator(...)`). Hang hooks on `Validator`
or the compose root. No multiple inheritance of leaves, no Cap Host, no
`rule/`. Path helpers and async-bridge names are not in the package `__all__`.
