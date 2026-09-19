# ux-valio

The validator **is** the dataclass field default:

```python
name: str = StringValidator(max_length=50)
```

Greenfield reimplementation of
[`bitplorer/valio`](https://github.com/bitplorer/valio) frozen at
[`3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
There is no Field twin and no Schema twin. Valio itself is not edited.

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
    name: str = StringValidator(max_length=50, required=True)
    rank: str = Validator(in_choice=["Male", "Female", "Trans"], default="Female")
    n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)
```

`Validator[int]` is the same descriptor with the stored type on it.
Use it on a plain class (no field annotation) or next to `n: int` — the
two must agree. `IntegerValidator` is already `Validator[int]`. An
unconstrained `TypeVar` (`item: T = Validator()` on a generic class) is
typing-only; runtime cannot specialize one descriptor per `Box[int]` /
`Box[str]`.

```python
class Stats:
    n = Validator[int](min_value=0)
```

A `TypedDict` is the schema (stdlib, no BaseModel). Extra keys fail-closed.
`total=False` and PEP 655 `Required` / `NotRequired` are the TypedDict
metaclass (`__required_keys__`) — hang extras with `Annotated`, or the same
assignment as a dataclass (`name: str = StringValidator()`), then
`@name.pre_validate` / `@name.validator` in the TypedDict
body. `self` in those hooks is the mapping. No Schema twin.

```python
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

Concern leaves (`LengthValidator`, `RequiredValidator`, …) are the **advanced**
path: compose validator objects with `&` (AllOf) / `|` (AnyOf), or explicit
`AllOf` / `AnyOf`, as **one** descriptor. `Chain` is `AllOf` — an alias, not a
third AND. Facades do not multiple-inherit leaves.

```python
from ux_valio import LengthValidator, RequiredValidator

tag: str = LengthValidator(min_length=3) & RequiredValidator(required=True)
```

Hang `pre_validate` / `validator` / `post_set` / `task_*` on the field name. The descriptor *is* the dataclass default —
no outer `username_field` twin, no Field mixin. Those methods live on
`ValidateProperty` (leaf or facade). Do not invent `pre_set` as a hang —
`_run_pre_set` *is* the validate pipeline.

### Hang API

Process is the default kind (pipeline must finish). `task_*` is background
(setter does not wait). `validator` is a check during `validate()`
(attrs `@x.validator`; return ignored). Sync or async.

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

`&` / `|` return `AllOf` / `AnyOf` from `ValidateProperty` — same module
as the operators, no per-use import.

```python
@dataclass
class User:
    name: str = StringValidator(max_length=50) & RequiredValidator(
        required=True
    )

    @name.pre_validate
    def strip(self, value: str) -> str:
        return value.strip()

    @name.validator
    def not_blank(self, value: str) -> None:
        if not value:
            raise ValueError("blank")
```

Runtime the instance sees `str`. Construction is `Any` to type checkers
(`ValidateProperty.__new__`; mypy via `plugins = ["ux_valio.mypy_plugin"]`)
so `StringValidator()` assigns to `str` and a custom `UserValidator()`
assigns to `User`. No per-type mixin. `User(name=1)` still errors.
`@name.pre_validate` may underline (the annotation is `str`).

A new store type is a subclass and an `annotation`. Optional needs
`| None` on **both** sides — `Account` vs `Account | None` is a conflict
(same as `int` vs `int | None`). A subclass owner (`Admin(Account)`)
binds (`is_subclass_of` at bind, `is_instance_of` at set).

```python
class Account:
    ...

class AccountValidator(Validator[Account]):
    annotation = Account | None

@dataclass
class Row:
    owner: Account | None = AccountValidator(default=None)
```

Class access `User.name` is that descriptor, so `User.name.post_set`
also works after the class exists. Dataclass uses the descriptor as the
field default; assigning it is treated as unset and applies `default` /
`default_factory`. A shared descriptor (`aadhaar` on Person and Vendor)
uses the class you accessed: `Person.aadhaar.pre_validate` registers under Person,
not the last `__set_name__`.

## KEEP: debug swallow, logger OFF

- Omitted `debug` is `True` (re-raise). `debug=False` swallows, appends to
  `errors`, and leaves the attribute unset so later reads are `None`.
  Never-set `__get__` / `__delete__` with debug on raises a named
  `AttributeError` (`Cls.field is not set`), not a bare `KeyError`.
  This swallow is KEEP. Pass `debug=False` to opt in.
- Omitted `collect_all` is `True`: remaining concerns continue. One failure
  re-raises as itself; two or more surface as `ValidationErrors` (debug on)
  or as multiple entries on `errors` (debug off). `collect_all=False` is
  fail-fast. Do not overload `debug` into collect-all.

  ```python
  n: int = IntegerValidator(min_value=0, max_value=10, multiple_of=2)
  ```
- Composing members that specify different `debug`, `default`, or
  `default_factory` values raises `TypeError`. A right-hand `debug=True`
  is not discarded into swallow.
  Explicit `collect_all=False` / `logger=False` is specified: it TypeErrors
  against explicit `True`. An omitted `collect_all` / `logger` /
  `debug` stays unspecified (resolved True / OFF / True) so it still
  collapses to a specified `True`.
- `logger` defaults **OFF** (`False`). `logger=True` binds a stdlib
  `logging.Logger` at `__set_name__` named `module.qualname.field`.
  No files, no `logs/` directory — valio wrote files; pass your own
  `Logger` for that. `logger=None` is OFF, not valio's None=on.
  Get/set/delete log at info; failures at error. A field-level logger is
  the usage pattern Pydantic does not have.
- `|` is OR: `IntegerValidator | StringValidator` is AnyOf. Conflicting
  member annotations do not TypeError. The compose root does not AND-run a
  type check before alternatives. `&` / `AllOf` still TypeErrors on
  conflicting member annotations.

**Only the before-store pipeline return is stored.** That pipeline *is*
`pre_validate → validate → post_validate`. There is no `_processors["pre_set"]`
bag and no hang named `pre_set` — hang before-store work on `pre_validate`
(transform; **return the value**), `validator` (check; return ignored),
or `task_pre_validate` (background side effect; return ignored; setter
does not wait). Persist/reserve that must fail-closed hangs on
`post_set`. Welcome-email hangs on `task_post_set`.
Tasks are sync or async; they run on a process-held pool, not the
nest-safe processor worker. `from ux_valio import wait_tasks` waits for
them (tests / shutdown). A free function on an unbound descriptor takes
`namespace=Host` (the class), not a hand-built string key.

`pre_validate` / `task_*` accept **sync or async** callables. `async def`
registers. Coroutine **objects** at run are not a second reject path: same
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

valio README taught this on a Field factory (`@user_field.add_pre_valiator` — typo
for `pre_validate`). Hang the same processor on the **field
name**. Do **not** invent `add_pre_set`. A uniqueness **task** is the wrong
hook — return the value from `pre_validate`.

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
    username: str = StringValidator(required=True, min_length=3)

    @username.pre_validate
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
class: on an **unbound** descriptor `pre_validate` without `namespace=` is
`TypeError`; on a bound field (`Register.username.pre_validate`) the owner key is
the bound owner. `namespace=` is the owning class, or its
`module.qualname` str — not a hand-built bare `__name__`.
`namespace="Register"` is not rewritten to match lookup. A processor that forgets to
return the value stores `None`; return the value from `pre_validate`.

Assigned `0` / `False` / `""` are not replaced by `default`. `None` is.
`default=[]` is the same list on every instance. `default_factory=` is a
zero-arg callable invoked on each None assignment (dataclass-shaped, still
the descriptor — not a Field twin). Setting both is `TypeError`.
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

`post_validate` may transform after checks. If the field has an
annotation, the stored value must still match it — a post processor cannot
smuggle a `str` onto `IntegerValidator`. Named facades (`EmailValidator`,
`PaymentCardValidator`, `DateValidator`, …) re-check their extra on the
to-store value: post_validate cannot turn a valid email into `"not-an-email"`.
`AllOf` re-checks member named extras. `AnyOf` still has to match one
alternative. Untyped `Validator()` does not gate. Path bounds (`min_length`,
…) on AllOf / unnamed facades are not re-run. Custom `validator`
callables are not re-run.

`__get__` `post_get` runs in `finally`. A failing post_get is recorded; it
does not replace an in-flight never-set `AttributeError` when `debug=True`.

`PatternValidator` matches with `re.findall` (findall substring), not `fullmatch`.
Empty-match patterns (`a*`, `?`) still count as a match — that is the findall
engine, not a fullmatch. `EmailValidator` keeps that engine for its `pattern=`
path and then requires
the whole string to be an addr-spec: `"prefix user@example.com suffix"`
is rejected. Pattern `&` / `|` is
fail-closed on a missing fragment or mixed `str`/`bytes`; same-kind bytes
fragments concatenate as bytes. `count_min > count_max` is constructor
`ValueError`. A bytes pattern matches bytes (it is not `str()`-coerced).

Pattern lives in the `ux_valio.pattern` package. The taught import is still
the package root (`from ux_valio import Pattern, Digit, StartsWith, SetOf`).
`from ux_valio.pattern import Pattern` is the same objects — a package
re-home, not a second API. `WordBoundary` stays an atom `\b`.

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
    sku: str = PatternValidator(pattern=sku)
    tint: str = PatternValidator(pattern=hex_pair)
```

Runnable production skeletons live under `examples/` (`python examples/<file>.py`).
Each file is a service that injects Protocol ports in the constructor, plus a
dataclass callers can copy. `main()` is only the runnable runner.
Hooks (`pre_validate` / `post_set`) fail closed into validation
errors (uniqueness, password confirm, promo/inventory, payment gateway, KYC
registry). Password hashing is an example `PasswordHasher` port (stdlib
PBKDF2 demo); production replaces it with bcrypt/argon2id. In-memory fakes
keep the demos offline; examples do not ship a DB driver. Omitted `debug` /
`collect_all` are True; signup surfaces `ValidationErrors` when a field
fails more than one concern.

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
`EnumValidator` / `IntegerEnumValidator` / `StringEnumValidator`.

Named identity facades (`PaymentCardValidator`, `AadhaarCardValidator`,
`PANCardValidator`, `ExpiryValidator`, `PhoneNumberValidator`, …) run
their extra from `validate()` after the inherited path. They do not
register that check with `validator` on each assignment. That extra
check joins the collected bag (`collect_all=False` restores fail-fast).

## Named identity facades

Same field-default pattern as `StringValidator`. Print grouping strips;
the **stored value is the compact identity**. `None` skips. Stdlib only —
no portal, no DNS, no BIN lookup. `help(GSTINValidator)` is the per-facade
contract. Source lives in sibling domain modules under `facades/named/`
(`india/` `{kyc,gst,registry,bank}`, `finance`, `catalog`, `contact`,
`device`, `portal`, `expiry`) —
`from ux_valio.facades.named.india.gst import GSTINValidator` is
navigation; the taught import is still `from ux_valio import GSTINValidator`.

```python
from dataclasses import dataclass
from ux_valio import (
    BICValidator,
    GSTINValidator,
    IBANValidator,
    ISBNValidator,
    MACAddressValidator,
)

@dataclass
class Counterparty:
    gstin: str = GSTINValidator()
    iban: str = IBANValidator()
    bic: str = BICValidator()
    isbn: str = ISBNValidator()
    mac: str = MACAddressValidator()

row = Counterparty(
    gstin="09 AAAPA1111F 1Z P",
    iban="GB82 WEST 1234 5698 7654 32",
    bic="deutdeff",
    isbn="978-0-306-40615-7",
    mac="aa:bb:cc:dd:ee:ff",
)
# gstin "09AAAPA1111F1ZP", iban compact, bic "DEUTDEFF",
# isbn "9780306406157", mac "AABBCCDDEEFF"
```

| facade | stores | identity |
|---|---|---|
| `AadhaarCardValidator` | 12 digits | Verhoeff; first digit 2–9 |
| `PANCardValidator` | 10 A–Z/digits | Luhn mod 26 |
| `GSTINValidator` | 15 A–Z/digits | Luhn mod 36, state 01–38 / 97 / 99 |
| `TANValidator` | 10 chars | ITD format |
| `CINValidator` | 21 chars | MCA `L`/`U` + ROC + state + year |
| `DINValidator` | 8 digits | MCA director id; leading zeros stay |
| `LLPINValidator` | 7 chars | MCA `AAA1234` |
| `UdyamValidator` | `UDYAM-XX-00-0000000` | MSME registration |
| `FSSAIValidator` | 14 digits | licence `1` / registration `2` |
| `VoterIdValidator` | 3 letters + 7 digits | EPIC |
| `IndianPassportValidator` | 1 letter + 7 digits | MEA passport number |
| `IFSCValidator` | 11 chars | `ABCD0XXXXXX` |
| `PinCodeValidator` | 6 digits | India Post, first 1–9 |
| `UPIIdValidator` | lowercase VPA | `local@handle` |
| `IBANValidator` | 15–34 chars | ISO 13616 mod-97 |
| `BICValidator` | 8 or 11 A–Z/digits | ISO 9362 / SWIFT |
| `ISINValidator` | 12 chars | ISO 6166 ∩ Luhn |
| `ISBNValidator` | 10 or 13 | ISBN-10 mod 11 / ISBN-13 978\|979 |
| `EANValidator` | 13 digits | GS1 check |
| `GTINValidator` | 8/12/13/14 digits | GS1 (UPC-A / EAN-8 / GTIN-14) |
| `HSNCodeValidator` | 4, 6, or 8 digits | GST HSN/SAC |
| `HostnameValidator` | lowercase FQDN | RFC 1123; not a URL; not IPv4 |
| `SlugValidator` | lowercase `foo-bar` | does not slugify spaces |
| `CurrencyCodeValidator` | 3 letters | ISO 4217 |
| `CountryCodeValidator` | 2 letters | ISO 3166-1 alpha-2 |
| `TimezoneValidator` | IANA key | `zoneinfo.available_timezones()` |
| `ULIDValidator` | 26 chars | Crockford base32 |
| `LEIValidator` | 20 chars | ISO 17442 mod-97 |
| `CardExpiryValidator` | `MMYY` | card print form; not wall-clock |
| `ABARoutingValidator` | 9 digits | ABA checksum |
| `VINValidator` | 17 chars | ISO 3779 check digit, no I/O/Q |
| `MACAddressValidator` | 12 hex | 48-bit; colon/hyphen/Cisco ok |
| `IMEIValidator` | 15 digits | Luhn |
| `PaymentCardValidator` | compact digits | brand ∩ Luhn (incl. UnionPay) |
| `EmailValidator` | given string | addr-spec **fullmatch** |
| `URLValidator` | given string | scheme + netloc |
| `ExpiryValidator` | field's store type | exclusive `expire_*` wall-clock |
| `PhoneNumberValidator` | given string | `region=` required; `phonenumbers` extra |

`PhoneNumberValidator` is a string facade. Pass `region="IN"` (required).
`ExpiryValidator(expire_before="2020-01-01")` — exactly one `expire_*`.

List / dictionary / set / tuple collection facades are not
shipped; `list[T]` / `dict[K, V]` membership is the type check.

Min/max length and value leaves (`MinLengthValidator`, `MaxLengthValidator`,
`MinValueValidator`, `MaxValueValidator`) are public building blocks.

`AttributeValidator` is **not** shipped. Check object attributes at the call
site or with `validator`. RGB/HSL color validators are retired.
`HexColorValidator` is not a public facade.

## From valio's Field factory

Valio README taught a second shape: construct a `*Field`, hang decorators on
it, then assign `password: str = password_field.validator`. That Field factory
duplicated kwargs, dropped `gt`/`lt`/`eq`/`multiple_of`/`in_choice` from its
signature, and is untested. ux-valio does not ship it. Move the kwargs onto
`StringValidator` / `IntegerValidator` / `Validator` as the dataclass default,
and hang `pre_validate` / `validator` on that descriptor. Star-import
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
