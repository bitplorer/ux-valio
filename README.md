# ux-valio

The validator **is** the dataclass field default:

```python
name: str = StringValidator(debug=True, max_length=50)
```

Greenfield reimplementation of
[`bitplorer/valio`](https://github.com/bitplorer/valio) frozen at
[`3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
Valio called this shape **Door A** (vs a Field/Schema twin this library
does not ship). Valio itself is not edited.

## Install

Python ≥ 3.14 (same floor as `ux-compose`).

```console
pip install -e .
```

## Usage

The taught caller shape is a **typed facade or `Validator`** as the dataclass
field default. `field: T = SomeValidator(...)` is the whole API. There is no Field
twin and no Schema twin. Do not use bare `Property` as the field default —
it is the descriptor base, not a product facade.

```python
from dataclasses import dataclass
from ux_valio import IntegerValidator, StringValidator, Validator

@dataclass
class User:
    name: str = StringValidator(debug=True, max_length=50, required=True)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2, debug=True)
```

`Validator[int]` is the same door with the stored type on the descriptor.
Use it on a plain class (no field annotation) or next to `n: int` — the
two must agree. `IntegerValidator` is already `Validator[int]`. An
unconstrained `TypeVar` (`item: T = Validator()` on a generic class) is
typing-only; runtime cannot specialize one descriptor per `Box[int]` /
`Box[str]`.

```python
class Stats:
    n = Validator[int](min_value=0, debug=True)
```

Concern leaves (`LengthValidator`, `RequiredValidator`, …) are the **advanced**
path: compose validator objects with `&` (AllOf) / `|` (AnyOf), or explicit
`AllOf` / `AnyOf`, as **one** descriptor. `Chain` is `AllOf` — an alias, not a
third AND. Facades do not multiple-inherit leaves.

```python
from ux_valio import LengthValidator, RequiredValidator

tag: str = LengthValidator(min_length=3, debug=True) & RequiredValidator(required=True)
```

Hang `add_*` on the field name. The descriptor *is* the dataclass default —
no outer `username_field` twin, no Field mixin. `add_*` lives on
`ValidateProperty` (leaf or facade). Do not invent `add_pre_set`.

`&` / `|` return `AllOf` / `AnyOf` from `ValidateProperty` — same module
as the operators, no per-use import.

```python
@dataclass
class User:
    name: str = StringValidator(debug=True, max_length=50) & RequiredValidator(
        required=True
    )

    @name.add_process_pre_validate
    def strip(self, value: str) -> str:
        return value.strip()
```

Class access `User.name` is that descriptor, so `User.name.add_process_post_set`
also works after the class exists. Dataclass uses the descriptor as the
field default; assigning it is treated as unset and applies `default` /
`default_factory`. A shared descriptor (`aadhaar` on Person and Vendor)
uses the class you accessed: `Person.aadhaar.add_*` registers under Person,
not the last `__set_name__`.

## KEEP: debug swallow, logger OFF, pre_set hook

- `debug=True` re-raises on a failed set/get/delete.
- Never-set `__get__` or `__delete__` with `debug=True` raises a named
  `AttributeError` (`Cls.field is not set`), not a bare `KeyError`.
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
- Composing members that specify different `debug`, `default`, or
  `default_factory` values raises `TypeError`. A right-hand `debug=True`
  is not discarded into swallow.
  Explicit `collect_all=False` / `logger=False` is specified: it TypeErrors
  against explicit `True`. An omitted `collect_all` / `logger` (runtime
  default False / OFF) still collapses to a specified `True`. `debug` stays
  fail-closed (`None` is unspecified).
- `logger` defaults **OFF** (`False`). `logger=True` binds a stdlib
  `logging.Logger` at `__set_name__` named `module.qualname.field`.
  No files, no `logs/` directory — valio wrote files; pass your own
  `Logger` for that. `logger=None` is OFF, not valio's None=on.
  Get/set/delete log at info; failures at error. A field-level logger is
  the usage-pattern door Pydantic does not have.
- `|` is OR: `IntegerValidator | StringValidator` is AnyOf. Conflicting
  member annotations do not TypeError. The compose root does not AND-run a
  type check before alternatives. `&` / `AllOf` still TypeErrors on
  conflicting member annotations.

**Only the descriptor `pre_set` hook return is stored.** That hook *is*
`pre_validate → validate → post_validate`. There is no `_processors["pre_set"]`
bag and no `add_pre_set` — hang before-store work on `add_process_pre_validate`
(transform; **return the value**), `add_validator` (check; return ignored),
or `add_task_pre_validate` (background side effect; return ignored; setter
does not wait). Persist/reserve that must fail-closed hangs on
`add_process_post_set`. Welcome-email hangs on `add_task_post_set`.
Tasks are sync or async; they run on a process-held pool, not the
nest-safe processor worker.

`add_process_*` / `add_task_*` accept **sync or async** callables. `async def`
registers. Coroutine **objects** at run are not a second reject door: same
run rules as `async def`.

**Run rules:** on the sync descriptor path,
- no running loop → `TypeError` (`async callable needs a running event loop / helper`).
  Not silent `None`, not `asyncio.run`.
- running loop → nest-safe sync-bridge (process-held worker pool, private
  loop in a worker thread; not a public dial).
  Assign from an async context (`asyncio.run` of a small harness or
  pytest-asyncio). Same-thread `run_until_complete` on the caller's loop
  is a nested-loop hazard. Re-entering the nest-safe worker is `TypeError`
  (would deadlock), not a hang.

`asyncio.run` is not used in `__set__`.

### Before-store DB check (Register)

valio README taught this on Door B (`@user_field.add_pre_valiator` — typo
for `add_process_pre_validate`). Hang the same processor on the **field
name**. Do **not** invent `add_pre_set`. A uniqueness **task** is the wrong
hook — return the value from `add_process_pre_validate`.

Class-body `username: str = username` is `NameError` only when an outer
name collides with the field (the assignment makes `username` local).
Hang on the field name after it is assigned. An outer `username_field`
is only needed when **sharing** one descriptor across classes.

```python
from dataclasses import dataclass
from ux_valio import StringValidator

DB = {"taken"}

@dataclass
class Register:
    username: str = StringValidator(debug=True, required=True, min_length=3)

    @username.add_process_pre_validate
    def username_not_taken(self, value: str) -> str:
        if value in DB:
            raise ValueError("username already registered")
        return value
```

Processor and task registries use one key on register and lookup: the owning
class’s `module.qualname` (`f"{cls.__module__}.{cls.__qualname__}"`). Two
classes named `User` in different modules do not share hooks — the old bare
`__name__` key was a collision. A method decorator derives that key from the
method (nested classes included). Lookup walks the instance MRO (base first),
so a child dataclass runs parent field hooks. A free function has no owning
class: on an **unbound** descriptor `add_*` without `namespace=` is
`TypeError`; on a bound field (`Register.username.add_*`) the owner key is
the bound owner. `namespace=` is that owner key
as-is; it fires only when that string equals the instance class’s
`module.qualname` (or an MRO parent). Passing a class object as `namespace=` is `TypeError`
(string keys only). Leftover teaching: `namespace="Register"` (bare
`__name__`) is not rewritten to match lookup. A processor that forgets to
return the value stores `None`; return the value from `add_process_pre_validate`.

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
`default=[]` is the same list on every instance. `default_factory=` is a
zero-arg callable invoked on each None assignment (dataclass-shaped, still
the descriptor door — not a Field twin). Setting both is `TypeError`.
Leftover: a callable `default=` is still invoked, so `default=list` already
built a new list; prefer `default_factory=list` when the intent is
per-instance.
Bound `0` is specified: `min_value`/`max_value` inclusive, `gt`/`lt`
exclusive, `multiple_of` is remainder, `multiple_of=0` accepts only `0`.
`in_choice` / `not_in_choice` skip `None` (optional unset). A string used
as `in_choice` must not TypeError on that skip.

The field stores on `instance.__dict__`. Explicit `__slots__` that include the
field TypeError at bind. A slots-only class (no `__dict__` in the MRO)
TypeErrors at bind even when the field name is not a slot. A child that
does not define `__slots__` still has `__dict__`. `@dataclass(slots=True)`
is unsupported: dataclass replaces the descriptor after bind, and
validation would not run. `@dataclass(frozen=True)` works: dataclass
intercepts assign/delete with `FrozenInstanceError`; `__init__` still
runs the field descriptor.

`add_process_post_validate` may transform after checks. If the field has an
annotation, the stored value must still match it — a post processor cannot
smuggle a `str` onto `IntegerValidator`. Named facades (`EmailValidator`,
`PaymentCardValidator`, `DateValidator`, …) re-check their extra on the
to-store value: post_validate cannot turn a valid email into `"not-an-email"`.
`AllOf` re-checks member named extras. `AnyOf` still has to match one
alternative. Untyped `Validator()` does not gate. Path bounds (`min_length`,
…) on AllOf / unnamed facades are not re-run. Custom `add_validator`
callables are not re-run.

`__get__` `post_get` runs in `finally`. A failing post_get is recorded; it
does not replace an in-flight never-set `AttributeError` when `debug=True`.

`PatternValidator` matches with `re.findall` (findall substring), not `fullmatch`.
Empty-match patterns (`a*`, `?`) still count as a match — that is the findall
engine, not a fullmatch door. `EmailValidator` keeps that engine for its `pattern=`
path and then requires
the whole string to be an addr-spec: `"prefix user@example.com suffix"`
is rejected. Pattern `&` / `|` is
fail-closed on a missing fragment or mixed `str`/`bytes`; same-kind bytes
fragments concatenate as bytes. `count_min > count_max` is constructor
`ValueError`. A bytes pattern matches bytes (it is not `str()`-coerced).

Pattern lives in the `ux_valio.pattern` package. The taught import is still
the package root (`from ux_valio import Pattern, Digit, StartsWith, SetOf`).
`from ux_valio.pattern import Pattern` is the same objects — a package
re-home, not a second door. `WordBoundary` stays an atom `\b`.

Thin PatternTypes evidenced in valio@3415c03 `valio/regexer/regexps.py`.
Those names are the taught PatternType atoms (KEEP; not `DigitAtom` /
`CharacterClass` / `Lookbehind`):

- `StartsWith` / `EndsWith` (`^` / `$`) at L414 / L421
- lookarounds `IfPrecededBy` / `IfNotPrecededBy` / `IfFollowedBy` /
  `IfNotFollowedBy` at L449–L470
- `SetOf` character-class `[raw]` / `[^raw]` at L261 (`~SetOf(...)` negates)

`Contained` / `IfContained` are KEEP-absent: they do not exist in
valio@3415c03. Capturing groups, `WordGroups`, `scanString`, pyparsing,
and a second `regexer` package are not ported.

```python
from dataclasses import dataclass
from ux_valio import Digit, Pattern, PatternValidator, SetOf, StartsWith

sku = StartsWith(Pattern(r"INV-")) & Digit(count=4)
hex_pair = SetOf(Pattern(r"0-9a-f"), count=2)

@dataclass
class Part:
    sku: str = PatternValidator(pattern=sku, debug=True)
    tint: str = PatternValidator(pattern=hex_pair, debug=True)
```

Runnable production skeletons live under `examples/` (`python examples/<file>.py`).
Each file is a service that injects Protocol ports in the constructor, plus a
dataclass callers can copy. `main()` is only the runnable runner.
Hooks (`add_process_pre_validate` / `add_process_post_set`) fail closed into validation
errors (uniqueness, password confirm, promo/inventory, payment gateway, KYC
registry). Password hashing is an example `PasswordHasher` port (stdlib
PBKDF2 demo); production replaces it with bcrypt/argon2id. In-memory fakes
keep the demos offline; examples do not ship a DB driver. `debug=True` is
fail-closed; signup uses `collect_all=True` and `ValidationErrors`.

Owner annotations that are still strings or `ForwardRef` (including
`from __future__ import annotations`) fail at class body with `TypeError`.
They are not copied onto the descriptor and are not `eval`'d. Drop postponed
annotations on these fields, or the bind stays closed.

Typed facades (`IntegerValidator`, …) conflict with `int | None` / `int | str`
at class body. Use `Validator()` for optional/union fields, or `|` AnyOf of
matching facades.

An unknown validation-path unit raises `ValueError`, not `KeyError`.

`DateValidator` stores `datetime.date`. Numeric EU (`YYYY-MM-DD`, also
`/` and `:`) and IND (`DD-MM-YYYY`, also `/` and `:`) strings parse on
assignment; the same delimiter must appear on both sides. `02/01/2020`
is 2 January 2020 (IND), not 1 February (US). Month names, ordinals,
dots, and pyparsing `scanString` from valio `relib/dates.py` are not
ported. `datetime.datetime` is still rejected after the inherited path.
`DateTimeValidator` stores `datetime.datetime`. ISO strings parse with
`datetime.fromisoformat` (`2020-01-02T12:00:00`). Plain `datetime.date`
is rejected. `URLValidator` stores a `str` whose identity is scheme +
netloc (`https://example.com`); a scheme-less host is rejected.

## Typed facades

`IntegerValidator`, `StringValidator`, `BooleanValidator`, `FloatValidator`,
`DecimalValidator`, `BytesValidator`, `DateValidator` (`datetime.date`;
EU `YYYY-MM-DD` / IND `DD-MM-YYYY` numeric strings with `-` `/` `:` parse
to `date` and are stored as `date`; `datetime.datetime` is rejected;
owner annotation may be `date`, `str`, or `T | str`),
`DateTimeValidator` (`datetime.datetime`; ISO via `fromisoformat`;
plain `date` is rejected; owner may be `datetime`, `str`, or the union),
`EmailValidator`
(identity fullmatch extra on the compiled pattern; PatternValidator stays findall),
`URLValidator` (scheme + netloc identity),
`UUIDValidator` (coerces UUID strings; stores `uuid.UUID`; owner
annotation may be `uuid.UUID`, `str`, or `uuid.UUID | str`),
`PathValidator` (stores `pathlib.Path`; coerces `str` → `Path`;
owner may be `Path`, `str`, or the union; `path_exists=True` requires
the path to exist), `DecimalValidator` (coerces Decimal strings; rejects
float),
`IPv4Validator` / `IPv6Validator` / `IPAddressValidator`,
`EnumValidator` / `IntegerEnumValidator` / `StringEnumValidator`,
`PaymentCardValidator` (Visa / Mastercard / Amex / Discover / Rupay, each
Luhn **and** brand; a Luhn-valid non-brand number is rejected),
`AadhaarCardValidator` (12 digits ∩ Verhoeff checksum; a substring or
wrong-length value is rejected), `PANCardValidator` (10-character identity
`fullmatch` ∩ Luhn mod 26; a format-only generator is rejected), and
`ExpiryValidator` (`expire_after` / `expire_on` / `expire_before` are
exclusive; a bad `expire_before` string is checked on that kwarg, not on
`expire_after`). `expire_*` are not accepted on `Validator`. There is no
`expiry` path unit — the check lives on the facade.

Named typed facades (`DateValidator`, `PathValidator`, IP, `PaymentCardValidator`,
`AadhaarCardValidator`, `PANCardValidator`, `ExpiryValidator`,
`PhoneNumberValidator`) run their
extra check from `validate()` after the inherited path. They do not
register that check with `add_validator` on each assignment. With
`collect_all=True`, that extra check joins the collected bag instead of
being skipped after an inherited failure.

```python
from dataclasses import dataclass
from ux_valio import (
    AadhaarCardValidator,
    ExpiryValidator,
    PANCardValidator,
    PaymentCardValidator,
    PhoneNumberValidator,
)

@dataclass
class Card:
    number: str = PaymentCardValidator(debug=True)
    aadhaar: str = AadhaarCardValidator(debug=True)
    pan: str = PANCardValidator(debug=True)
    # expire_before is its own bound; do not also pass expire_after.
    until: str = ExpiryValidator(expire_before="2020-01-01", debug=True)
    # leftover: valio defaulted to instance.region or "IN"; pass region=.
    phone: str = PhoneNumberValidator(region="IN", debug=True)
```

`PhoneNumberValidator` is a string facade. `region=` is the taught
region (ISO 3166-1 alpha-2 as understood by `phonenumbers`). It is
required: there is no silent `"IN"` default and no `instance.region`
lookup. The engine is the optional extra `phonenumbers`
(`pip install ux-valio[phonenumbers]`); there is no network lookup
(no carrier / geocoder). `region` is not a kwarg on `Validator`.
List / dictionary / set / tuple collection facades are not
shipped; `list[T]` / `dict[K, V]` membership is the type check.

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
and hang `add_process_pre_validate` / `add_validator` on that descriptor. Star-import
of valio's 306 names is gone; import the names in `__all__`.

## Public surface

`Validator`, typed facades, concern leaves, `AllOf` / `AnyOf` (`Chain` is
`AllOf`, not a third AND), `ValidationErrors`, and `Pattern` / `PatternType`
combinators (`&` / `|`) plus stdlib atoms `Digit` / `Word` / `NonDigit` /
`NonWord` / `WhiteSpace` / `NonWhiteSpace` / `WordBoundary`, anchors
`StartsWith` / `EndsWith`, lookarounds `IfPrecededBy` / `IfFollowedBy` (and
the `IfNot*` pair), and `SetOf` character classes. The taught field default
is a facade or `Validator`, not bare `Property`. Concern leaves also compose
as validator objects (`LengthValidator(...) & RequiredValidator(...)`). Hang
hooks on the field default (`ValidateProperty`). No multiple inheritance of leaves,
no Cap Host, no `rule/`. Path helpers and async-bridge names are not in the
package `__all__`. Import Pattern names from `ux_valio` (or `ux_valio.pattern`
for the same objects). There is no `ux_valio.regexer`.
