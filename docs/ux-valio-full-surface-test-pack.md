# ux-valio full-surface test pack

CARTGRAPH ONLY. No product tip. Frozen valio is read-only.

Council can ACCEPT the product worklist from this file alone. This draft is
KEEP-HEAD: **do not merge onto product `main`**. Same vehicle as packs #10 /
#12 / #13 / #16.

## Identity (verified)

| Item | Value |
| --- | --- |
| Started-from `origin/main` after `git fetch origin main` | **`a6c68763967a956e3cf4b13f3f44529446d80697`** |
| `git log -1` | `a6c6876 Named AttributeError on never-set get; add default_factory (#17)` |
| Claimed #17 merge | **`a6c6876`** — equals `origin/main` after fetch |
| valio PARKED | [`3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4) — not edited |
| Suite | **276 passed** / 23 files / Python 3.12.3 (`python3 -m pytest tests --override-ini addopts= -q`) |
| Floor | `requires-python = ">=3.10"` (`pyproject.toml`) |
| Barrels | `ux_valio.__all__` **47** (including `__version__`); `validators.__all__` **38** (subset of the top barrel) |
| Product tip | **HOLD** until Council CLEAR on this pack. No product PR opened. |

Parent teaching still on main: #14 bind / AnyOf / merge / path; #15 Aadhaar / PAN / Pattern atoms; #17 never-set named `AttributeError` + `default_factory`.

## Human ask

Full end-to-end review of every public validator / Pattern / compose form,
every constructor parameter, behaviour vs intent, holes / bugs / residuals.
Then (Phase B, **HOLD**) expand tests and fix clear defects — without inventing
a second product.

## Worklist (ACCEPT text)

### DO

No P0. Justified P1 (honesty locks on existing doors; no new public names):

1. **DateValidator vs `datetime.datetime`.** `datetime.datetime` is a
   `datetime.date` subclass, so the type door accepts datetimes.
   `ux_valio/validators/typed.py:44-47` sets `annotation = datetime.date` and
   does not reject the subclass. Measured: `When(d=datetime.datetime(...))`
   stores a datetime. Extra check from `validate()` after the inherited path
   (same named-facade shape as Path / IP / Payment).
2. **Pattern compose interpolates `None` / mixed types.**
   `ux_valio/pattern.py:59-73` (`AndPattern` / `OrPattern`) uses
   `f"{first.pattern}{second.pattern}"`. Empty `PatternType()` has
   `pattern is None` (`pattern.py:36-39`). Measured: `PatternType() & Digit()`
   → `'None\\d'`; `Pattern(b"a") & Pattern("b")` → `"b'a'b"`; even
   `Pattern(b"a") & Pattern(b"b")` becomes the str `"b'a'b'b'"`. Fail-closed
   TypeError on missing or mixed `str`/`bytes` fragments; same-kind bytes
   concatenate as bytes.
3. **Inverted Pattern repeats.** `_quantifier` (`pattern.py:76-105`) rejects
   `count` with `count_min`/`count_max` and `count_min < 0`, but not
   `count_min > count_max`. Measured: `Pattern(r"a", count_min=5, count_max=2)`
   builds `a{5,2}` and `re.compile` raises `re.error` later. Constructor
   `ValueError`.
4. **PatternValidator bytes identity.** `_validate_pattern`
   (`ux_valio/validators/leaves.py:163-173`) does
   `text = value if isinstance(value, str) else str(value)` then
   `re.compile(source).findall(text)`. Measured: `BytesValidator(pattern=b"ab")`
   TypeError (`cannot use a bytes pattern on a string-like object`);
   `BytesValidator(pattern="ab")` happens to pass because `str(b"ab")` is
   `"b'ab'"` which findall-matches `"ab"`. Match `str` against `str` and
   `bytes` against `bytes`; mixed TypeError; do not `str()` bytes.
5. **Named-facade extra checks vs `collect_all`.** Extra checks run *after*
   `super().validate()` (`typed.py:83-89` Path, `92-128` IP;
   `payment.py:57-65`; `aadhaar.py:58-66`; `pan.py:40-48`; `expiry.py:75-77`).
   `Validator.validate` (`facade.py:113-125`) already `raise_collected`.
   Measured: `PaymentCardValidator(min_length=20, collect_all=True, debug=True)`
   with a 16-digit Visa reports **one** length error, not length ∩ brand.
   Same for `IPv4Validator(max_length=3, collect_all=True)`. Continue the extra
   check into the collected bag (still after the inherited path; still no
   `add_validator` self-registration).

### KEEP

- Door A only: `field: T = SomeValidator(...)`. No Cap Host, Field twin,
  Schema twin, `mount_channel`, `rule/`, Result type, RGB/HSL, star-import
  barrel.
- Debug swallow: `debug=True` re-raises; falsy including default `None`
  swallows, appends `errors`, leaves unset (`descriptor.py:10-14,169-178,218-245`).
- Never-set `__get__` / `__delete__` with `debug=True` is named
  `AttributeError` (`Cls.field is not set`), not bare `KeyError`
  (`descriptor.py:231-261`). Debug-falsy still reads back `None`.
- `logger` default OFF (`False`). `logger=None` is specified OFF, not valio’s
  file-logging `None` (`descriptor.py:112-121`).
- Falsy assigned `0` / `False` / `""` are not replaced by `default`.
  `default=[]` is shared. `default_factory=` is per-instance. Both set is
  TypeError. Callable `default=` is still invoked (valio leftover)
  (`descriptor.py:3-8,218-224`).
- Bound honesty: `None` unset, `0` specified (`bounds.py:9-11`). Inclusive
  min/max; exclusive `gt`/`lt`; `multiple_of=0` accepts only `0`.
- Pattern `findall` substring (not fullmatch). `EmailValidator` uses that
  door: `"prefix user@example.com suffix"` is accepted.
- `collect_all` default False (fail-fast). Do not overload `debug` into
  collect-all.
- Compose merge fail-closed on conflicting specified `debug` / `default` /
  `default_factory` / `collect_all` / `logger`. Explicit `False` is specified.
  Omitted `collect_all` / `logger` still collapse to a specified `True`.
  `debug` stays fail-closed (`None` unspecified) (`compose.py:32-54,96-113`).
- `Chain is AllOf` (`compose.py:238`). `&` / `AllOf` AND; `|` / `AnyOf` OR.
  AnyOf does not AND-gate root type and does not TypeError on conflicting
  member annotations. AllOf keeps annotation-conflict TypeError
  (`compose.py:116-131,214-270`).
- Unresolved owner `str` / `ForwardRef` TypeError at bind; not copied, not
  eval’d (`descriptor.py:196-204`).
- Unknown `ValidationPath` unit is `ValueError`, not `KeyError`
  (`path.py:67-69`).
- TypedDict membership fail-closed on the private helper. Callable origin
  checked; signature is not. Generic subclass instance params are not
  inspected (`leaves.py:30-92`; locked in `tests/test_generics_honesty.py`).
- `cache_task=` accepted on `Validator` and compose roots; cache behaviour
  RETIRE (stored, never skips re-checks) (`hooks.py:92-93`, `facade.py:58,79`).
- `add_*` hangs on `Validator` or the compose root, not concern leaves.
  `pre_set` hook IS the validate pipeline. No `add_pre_set` /
  `_processors["pre_set"]`. `add_*` accepts async def and coroutine results.
  Sync path with no running loop: TypeError naming the missing loop / helper.
  Running loop: nest-safe worker bridge. No `asyncio.run` in `__set__`.
  `enable_async` is unknown-kwarg TypeError.
- Bag keys `module.qualname` on register and lookup (`hooks.py:30-67`).
- Named typed facades call extra checks from `validate()` after the inherited
  path; they do not `add_validator` themselves on each assignment
  (`tests/test_named_validate_once.py`).
- PaymentCard = brand ∩ Luhn (stdlib `re`). Aadhaar = 12-digit identity ∩
  Verhoeff. PAN = identity `fullmatch` ∩ Luhn mod 26 (complete A–Z).
  Expiry = exclusive `expire_after` / `expire_on` / `expire_before`.
  `expire_*` are not kwargs on `Validator`. No `expiry` path unit.
- `expire_on` nanosecond / exact-datetime equality is valio parity KEEP
  (pack #12). Measured: `expire_on=date.today().isoformat()` still assigns
  because `datetime.now() == parsed` is almost never true (`expiry.py:86-89`).
- UUID / Path coerce lives on `pre_validation_processing` (descriptor path).
  Direct `.validate()` on a UUID string is type TypeError (pack #12 KEEP)
  (`typed.py:58-81`).
- Facades do not multiple-inherit concern leaves. `AttributeValidator` is
  not shipped. `HexColorValidator` is not a public facade.
- `PhoneNumberValidator` needs a `phonenumbers` engine **and** a region door
  — DEFER (named in #16; still true).
- List / dict / set / tuple collection facades KEEP-absent; `list[T]` /
  `dict[K, V]` membership is the type door.
- Pattern `WhiteSpace` / `NonWhiteSpace` DEFER (named in #16); `Pattern(r"\s")`
  already works. Do not invent atoms in the tip without CLEAR.
- Date strings / EU+IND PARTIAL KEEP: `DateValidator` is `datetime.date` only;
  strings are not parsed (`typed.py:44-47`).
- Integer / `TypeValidator` accepting `True` as `int` is Python `isinstance`
  honesty (locked `tests/test_descriptor_lifecycle.py:122-136`).
- `Property` is exported, not taught as the field default (README).
- Dual barrels are layered (`ux_valio` vs `validators` vs `pattern`), not
  synonyms. No rename pass.

### DEAD

Retired on purpose; do not re-park or resurrect:

- Door B Field factory / `field.validator` assignment.
- Cap Host / NamedOnce Cap / `mount_channel`.
- Schema twin / dual-schema `Union[T, Validator]` / typingx.
- `add_pre_set` / `_processors["pre_set"]` / `_reject_coroutine_result`.
- `asyncio.run` in `__set__`. `enable_async` as a door.
- `cache_task` *behaviour* (kwarg stays).
- Public `check_*` / `check_instance` / `regexer` / pyparsing.
- RGB / HSL / public `HexColorValidator`.
- Star-import of valio’s 306 names.
- Ceremony labels on the product surface.

### DO NOT

- Edit valio. The frozen tree stays parked at `3415c03`.
- Merge this pack, or packs #10 / #12 / #13 / #16, onto product `main`.
- Open or undraft a product tip PR until Council CLEAR.
- Invent new public API (no `WhiteSpace`, no Phone, no collection facades,
  no public `check_*`, no Cap / Field / Schema).
- Coerce inside `validate()` as a second product door (UUID / Path stay on
  `pre_validation_processing`).
- Overload `debug` into collect-all. Fail-open by flipping swallow off.
- Silent narrowing. L-monotonic: extra checks add constraints, they do not
  drop existing ones.

---

## Ranked defects

**P0: 0.** Spine locks (annotation conflict, never-set get, compose merge,
async hooks, bag keying, generics, collect_all, ValidationPath, named-once,
Aadhaar / PAN / Pattern atoms) still hold on `a6c6876`.

### P1 (fix on product tip after CLEAR)

| ID | Hole | Evidence |
| --- | --- | --- |
| A1 | `DateValidator` accepts `datetime.datetime` | `typed.py:44-47`; `isinstance(datetime, date) is True`; measured assignment stores a datetime |
| A2 | Pattern `&` / `|` interpolates `None` and mixed/`bytes` via `str` | `pattern.py:36-39,59-73`; measured `'None\\d'`, `"b'a'b"` |
| A3 | Inverted `count_min > count_max` is not constructor-closed | `pattern.py:90-100`; measured `a{5,2}` then `re.error` |
| A4 | PatternValidator `str()`-coerces non-str; bytes patterns cannot match bytes | `leaves.py:170-171`; measured `BytesValidator(pattern=b"ab")` TypeError |
| A5 | Named-facade extra checks skipped once `super().validate()` raise_collected | `facade.py:113-125` + Path/IP/Payment/Aadhaar/PAN/Expiry `validate()`; measured collect_all reports only length, not brand/IP |

### P2 (residuals / KEEP / coverage)

| ID | Item | Mark |
| --- | --- | --- |
| B1 | `expire_on` exact `datetime.now() == parsed` almost never fires | KEEP valio parity (`expiry.py:86-89`) |
| B2 | UUID/Path coerce only on descriptor path | KEEP (`typed.py:58-81`) |
| B3 | `cache_task` stored, never consulted | KEEP kwarg / RETIRE behaviour (`hooks.py:92-93`) |
| B4 | `number_of_assignment` incremented, unused for the reassign door | leftover counter (`facade.py:72-95`, `leaves.py:186-195`); reassign uses `_assignment_counts` |
| B5 | Reassignment counts keyed by `id(obj)` can leak if `__delete__` is never called | pack #12 P2; not a correctness lie while the instance lives |
| B6 | `ChoiceValidator.not_in_choice` does not skip `None`; `None in "abc"` is TypeError | `leaves.py:248-259`; `in_choice` skips `None` |
| B7 | Payment brands besides Visa are implementation-true, test-thin | `payment.py:13-51` vs `tests/test_payment_card.py` (Visa + Luhn-non-brand only). Probe accepted MC/Amex/Discover/Rupay Luhn vectors |
| B8 | `PatternValidator` compiles on every call | perf leftover, not a behaviour lie |
| B9 | `EnumValidator` copies owner annotation (including a mistaken `int`) | `typed.py:131-132`; type door then AND extra Enum check. Teaching leftover, not a new door |
| B10 | `PathValidator(min_length=…)` hits `len(Path)` TypeError | user combining length with Path; not a new API |
| B11 | Rejector / parity leftovers | **none still real** on this tree (no `Rejector` symbol; `_reject_coroutine_result` absent — locked `tests/test_async_callables.py:25-26`) |

---

## 1. Export inventory

Source: `ux_valio/__init__.py:54-102` (47 names).
`ux_valio/validators/__init__.py:43-82` (38 names) is a subset: Pattern
atoms and `Property` live only on the top barrel. Locked:
`tests/test_product_surface.py:110-112` (`validators.__all__ - ux_valio.__all__`
is empty).

### Door A facades (typed + fat)

| Export | Module | Class annotation / extra |
| --- | --- | --- |
| `Validator` | `validators/facade.py:30` | none until bind copies owner |
| `IntegerValidator` | `facade.py:128-129` | `int` |
| `StringValidator` | `facade.py:132-133` | `str` |
| `BooleanValidator` | `facade.py:136-137` | `bool` |
| `FloatValidator` | `typed.py:32-33` | `float` (rejects `int`) |
| `DecimalValidator` | `typed.py:36-37` | `decimal.Decimal` |
| `BytesValidator` | `typed.py:40-41` | `bytes` |
| `DateValidator` | `typed.py:44-47` | `datetime.date` (see A1) |
| `EmailValidator` | `typed.py:50-52` | `str` + default email Pattern (findall) |
| `UUIDValidator` | `typed.py:55-64` | `uuid.UUID`; str coerce on descriptor path |
| `PathValidator` | `typed.py:67-89` | `pathlib.Path`; str coerce; `path_exists=` |
| `IPv4Validator` | `typed.py:92-102` | `str` + `ipaddress.IPv4Address` |
| `IPv6Validator` | `typed.py:105-115` | `str` + `ipaddress.IPv6Address` |
| `IPAddressValidator` | `typed.py:118-128` | `str` + `ipaddress.ip_address` |
| `EnumValidator` | `typed.py:131-141` | unset class annotation; extra `enum.Enum` |
| `IntegerEnumValidator` | `typed.py:144-152` | extra `enum.IntEnum` |
| `StringEnumValidator` | `typed.py:155-163` | extra `Enum` with `str` value |
| `PaymentCardValidator` | `payment.py:54-65` | `str` + brand ∩ Luhn `fullmatch` |
| `AadhaarCardValidator` | `aadhaar.py:55-66` | `str` + 12 digits ∩ Verhoeff |
| `PANCardValidator` | `pan.py:37-48` | `str` + identity `fullmatch` ∩ Luhn mod 26 |
| `ExpiryValidator` | `expiry.py:62-95` | exclusive `expire_*`; check is *now* vs bound, not the assigned value as a date |

### Concern leaves (advanced `&` / `|`)

| Export | Module | Concern |
| --- | --- | --- |
| `TypeValidator` | `leaves.py:129-138` | owner / self `annotation` via `is_instance_of` |
| `RequiredValidator` | `leaves.py:141-155` | `required=True` rejects `None` only |
| `PatternValidator` | `leaves.py:158-176` | `re.findall` substring |
| `ReassignValidator` | `leaves.py:179-212` | `reassign=False` once per instance; counts drop on delete |
| `MultipleValidator` | `leaves.py:215-234` | remainder; `multiple_of=0` ⇒ value `== 0` |
| `ChoiceValidator` | `leaves.py:237-262` | `in_choice` / `not_in_choice` |
| `LengthValidator` | `length.py:52-101` | exact + inclusive min/max |
| `MinLengthValidator` | `length.py:12-29` | inclusive floor; `0` is a bound |
| `MaxLengthValidator` | `length.py:32-49` | inclusive ceiling |
| `ValueValidator` | `value.py:76-147` | min/max/gt/eq/lt/value |
| `MinValueValidator` | `value.py:12-41` | `min_value` xor `gt` |
| `MaxValueValidator` | `value.py:44-73` | `max_value` xor `lt` |

### Compose

| Export | Module | Behaviour |
| --- | --- | --- |
| `AllOf` | `compose.py:214-235` | AND; root type gate; flatten nested AllOf unless hooks / specified attrs differ |
| `AnyOf` | `compose.py:241-270` | OR; first success wins; no member-annotation merge; no root type AND-gate |
| `Chain` | `compose.py:238` | `AllOf` alias, not a third AND |

### Pattern algebra (not descriptors)

| Export | Module | Behaviour |
| --- | --- | --- |
| `PatternType` | `pattern.py:17-56` | fragment; `&` concat, `|` alternation |
| `Pattern` | `pattern.py:108-123` | fragment + quantifier kwargs |
| `Digit` / `Word` / `NonDigit` / `NonWord` | `pattern.py:156-169` | stdlib atoms `\d` `\w` `\D` `\W` with the same count kwargs |
| `WordBoundary` | `pattern.py:126-128` | atom `\b` (no count kwargs) |

`AndPattern` / `OrPattern` are return types of `&` / `|`, not in `__all__`.

### Descriptor / errors / version

| Export | Module | Role |
| --- | --- | --- |
| `Property` | `descriptor.py:87` | descriptor base; **not** the taught field default |
| `ValidateProperty` | `base.py:21` | ABC; `pre_set` is validate pipeline; `&` / `|` |
| `ValidationErrors` | `errors.py:12-24` | `collect_all=True` aggregate (`ValueError` subclass) |
| `__version__` | `__init__.py:52` | `"0.1.0"` |

Not exported (KEEP-absent / internals): `is_instance_of`, `ValidationPath`,
`HookHost`, async-bridge names, `AttributeValidator`, `HexColorValidator`,
`PhoneNumberValidator`, collection facades, public `check_*`.

---

## 2. Shared constructor parameters

### `Property` / `ValidateProperty` / `TypeValidator`

`descriptor.py:90-144`. Leaves that take `**kwargs` forward these.

| Param | Default | Specified? | What it does |
| --- | --- | --- | --- |
| `name` | `None` | set vs `None` | Bound at `__set_name__`. Mismatch with the owner field name is `AttributeError` (`descriptor.py:184-190`). |
| `default` | `None` | `is not None` | Applied only when the assigned value `is None`. Callables are invoked (valio leftover). |
| `default_factory` | `None` | `is not None` | Zero-arg callable per None assignment. Non-callable TypeError. Together with `default`: TypeError (`descriptor.py:132-137`). |
| `doc` | `None` | — | Stored; non-str TypeError. |
| `debug` | `None` | `is not None` | `True` re-raises. Falsy (including `None`) swallows. Non-bool TypeError. |
| `logger` | unset → `False` | `_logger_specified` | Default OFF. `None` → `False` but specified. `True` is specified and is a no-op in `_log` (`descriptor.py:164-167`). Else needs `.info`. |
| `collect_all` | unset → `False` | `_collect_all_specified` | Fail-fast unless `True`. Non-bool TypeError. Not a debug alias. |

`Property` does **not** take `cache_task` or concern kwargs. Unknown kwargs
TypeError (e.g. `annotation=`, `expire_before=`, `enable_async=`).

### `Validator` facade (+ typed subclasses)

`facade.py:35-88` plus `Property` params above.

| Param | Default | What it does |
| --- | --- | --- |
| `required` | `None` | `True` rejects `None` after default application. Non-bool TypeError. |
| `pattern` | `None` | `findall` via `PatternValidator._validate_pattern`. |
| `reassign` | `None` | `False` blocks a second assign until delete. Non-bool TypeError. Per-instance `_assignment_counts`; delete pops the id (`facade.py:90-99`). |
| `multiple_of` | `None` | Remainder; `0` only accepts `0`. |
| `min_value` / `max_value` | `None` | Inclusive. Conflict with `gt` / `lt`. |
| `gt` / `lt` | `None` | Exclusive. |
| `value` / `eq` | `None` | Exact; mutually exclusive; `eq` copies into `value` (`value.py:109-126`). |
| `min_length` / `length` / `max_length` | `None` | Inclusive / exact. Inverted bounds ValueError at construct. |
| `in_choice` / `not_in_choice` | `None` | Membership. `in_choice` skips `None`; `not_in_choice` does not (B6). |
| `cache_task` | `True` | Accepted; does not skip re-checks. |

Path order (`path.py:21-30`): reassignment → type → required → pattern →
multiple_of → length → value → choice, then `_run_custom_validators`.

### Extra facade kwargs

| Class | Extra | Notes |
| --- | --- | --- |
| `EmailValidator` | `pattern=` default `_EMAIL_PATTERN` | Overridable; findall KEEP |
| `PathValidator` | `path_exists: bool \| None = None` | `True` requires `path.exists()` after coerce; `False`/`None` skip |
| `ExpiryValidator` | `expire_after` / `expire_on` / `expire_before` | Mutually exclusive TypeError; bad string ValueError on **that** kwarg (`expiry.py:34-59`) |

### Compose roots

`AllOf` / `AnyOf` / `Chain`: `(*validators, cache_task=True, **kwargs)`.
At least two `ValidateProperty` members. Kwargs are the Property set
(`debug`, `default`, `default_factory`, `doc`, `logger`, `collect_all`) after
merge (`compose.py:96-152`).

### Leaves

Each leaf takes its concern arg(s) plus Property `**kwargs` (`debug`,
`default`, …). Leaves do **not** have `add_*` (`tests/test_compose_hooks.py:20-28`).

### Pattern atoms

`count` / `count_min` / `count_max` / `greedy=True` / `alias`. `count` cannot
mix with min/max. `WordBoundary` only `alias`.

### Hooks (`HookHost` — `Validator` and compose roots only)

`hooks.py:84-205`. Processor then task, once, per phase
(`pre_validate`, `post_validate`, `post_set`, `pre_get`, `post_get`,
`pre_delete`, `post_delete`). No `pre_set` bag.

| Method | Bag | Return |
| --- | --- | --- |
| `add_pre_validator` | processors `pre_validate` | **stored** (forgotten `return` stores `None`) |
| `add_post_validator` | processors `post_validate` | chained |
| `add_post_set` | processors `post_set` | ignored by descriptor |
| `add_pre_get` / `add_post_get` / `add_pre_delete` / `add_post_delete` | processors | get/delete pass `self.name`, not the stored value (`descriptor.py:24-25`) |
| `add_validator` | `_custom_validators` | check; return ignored |
| `add_*_task` | tasks of the matching phase | return ignored |

`namespace=` is the bag key as-is (`str`). Default is owning class
`module.qualname`. Free function without `namespace=` TypeError. Class-object
`namespace=` TypeError. Leftover: `namespace="Register"` (bare `__name__`) is
not rewritten to match lookup.

---

## 3. Suite (Phase A)

```text
python3 -m pytest tests --override-ini addopts= -q
276 passed in 0.32s
276 tests collected / 23 files / Python 3.12.3
```

Per-file:

| n | File |
| ---: | --- |
| 5 | `test_aadhaar_card.py` |
| 20 | `test_annotation_conflict.py` |
| 13 | `test_async_callables.py` |
| 23 | `test_bound_honesty.py` |
| 10 | `test_collect_all.py` |
| 18 | `test_compose_hooks.py` |
| 5 | `test_compose_not_inherit.py` |
| 15 | `test_descriptor_lifecycle.py` |
| 12 | `test_door_a_honesty.py` |
| 13 | `test_door_a_readme.py` |
| 10 | `test_expiry_validator.py` |
| 13 | `test_falsy_defaults.py` |
| 25 | `test_generics_honesty.py` |
| 22 | `test_hooks_namespace.py` |
| 4 | `test_named_validate_once.py` |
| 5 | `test_pan_card.py` |
| 9 | `test_path_fail_closed.py` |
| 13 | `test_pattern_findall.py` |
| 3 | `test_payment_card.py` |
| 5 | `test_processors_then_tasks.py` |
| 8 | `test_product_surface.py` |
| 11 | `test_typed_facades.py` |
| 14 | `test_validator_compose.py` |

No hypothesis / property tests. No load/chaos tests. `dev` extra is
`pytest>=7` only (`pyproject.toml`).

### Coverage vs each export (happy / param edge / fail-closed / compose)

Locked well: `Validator` / integer-string-boolean facades, length/value
bounds (including `0`), annotation conflict, postponed annotations, AnyOf vs
AllOf, compose merge (`debug`/`default`/`default_factory`/`collect_all`/`logger`),
hooks namespace, async run rules, generics `list`/`dict`/`tuple`/`Literal`/
`TypedDict`/`Callable` origin, collect_all vs debug, descriptor never-set /
delete / reassign, Aadhaar identity, PAN format∩checksum, Pattern findall +
Digit/Word atoms, named-once bags, product absences.

Thin or missing (Phase B after CLEAR — do not invent API):

- `ChoiceValidator` as a field default (`in_choice` / `not_in_choice` edges,
  None vs string haystack).
- `MultipleValidator` / min-max leaves as dataclass defaults (bounds are
  unit-tested via `.validate()`).
- Payment Mastercard / Amex / Discover / Rupay happy paths (implementation
  probed; tests are Visa-only).
- `DateValidator` vs `datetime.datetime` (A1 untested because it currently
  passes).
- Bytes + bytes `pattern` (A4).
- Pattern empty compose / mixed types / inverted counts (A2, A3).
- Named-facade `collect_all` including the extra check (A5).
- `expire_on` / `expire_before` future reject (before is tested as past-allow;
  after past-reject is tested).
- `logger=True` specified no-op; `doc=`; `name=` mismatch (mismatch is
  locked for reused descriptors).
- Feature: hook + `default_factory` + debug AttributeError in one lifecycle
  (pieces exist across files).
- Property-based length/bounds/type/pattern.
- Lightweight stress: many instances, nested compose depth, collect_all with
  many errors.

---

## 4. Behaviour vs locked tests vs valio@3415c03

Compare **functionality** gaps still named DEFER or holes. Do not re-park
named RETIRED (Door B, Cap, Field/Schema, public `check_*`, `add_pre_set`,
`asyncio.run` in `__set__`, ceremony labels).

| Valio@3415c03 / prior pack name | ux-valio `a6c6876` | Mark |
| --- | --- | --- |
| Door A descriptor-on-dataclass | COVERED | KEEP |
| Annotation conflict fail-closed | COVERED (#2, #14) | KEEP |
| Postponed annotations copied into type door | FIXED (#14 DO-1) | KEEP |
| AnyOf AND-gated root type | FIXED (#14 DO-2) | KEEP |
| Compose `collect_all`/`logger` False unspecified | FIXED (#14 DO-3) | KEEP |
| Unknown path unit `KeyError` | FIXED (#14 DO-4) | KEEP |
| Generics origin+args | COVERED (#11) | KEEP |
| Bag keys `module.qualname` | COVERED (#9) | KEEP |
| PaymentCard / Expiry / named-once | COVERED (#8) | KEEP |
| Aadhaar / PAN / Digit·Word·NonDigit·NonWord | COVERED (#15) | KEEP |
| Never-set get `KeyError` | FIXED (#17) | KEEP |
| `default_factory` | COVERED (#17) | KEEP |
| Async `add_*` / nest-safe bridge | COVERED (#5) | KEEP |
| `PhoneNumberValidator` | absent | DEFER (engine + region) |
| Collection facades | absent | KEEP-absent (`list[T]` type door) |
| Pattern WhiteSpace / NonWhiteSpace | absent | DEFER (`Pattern(r"\s")` works) |
| Date EU/IND string parse | absent | PARTIAL KEEP (`datetime.date` only) |
| Callable signature check | absent | DEFER |
| Generic subclass instance params | not inspected | KEEP |
| `expire_on` equality | same as valio | KEEP (B1) |
| UUID/Path coerce on `.validate()` | descriptor path only | KEEP (B2) |
| Field / Schema / Cap / HexColor / `check_*` | absent | DEAD / KEEP-absent |
| Pattern compose `None`/bytes (A2–A4) | **new hole** | P1 |
| Date vs datetime subclass (A1) | **new hole** | P1 |
| Named extra vs collect_all (A5) | **new hole** | P1 |

Rejector: no remaining symbol or reject-coroutine door.

---

## 5. Hole hunt (requested surfaces)

| Surface | Result on `a6c6876` |
| --- | --- |
| Annotation conflict | Locked. Owner vs facade TypeError at class body; `int \| None` vs `IntegerValidator` TypeError; unions agree via stdlib `get_origin`/`get_args`; postponed / `ForwardRef` TypeError at bind (`descriptor.py:180-216`; `tests/test_annotation_conflict.py`). |
| Never-set get | Locked named `AttributeError` (`descriptor.py:231-245`; `tests/test_descriptor_lifecycle.py:56-98`). |
| Compose merge | Locked for `debug` / `default` / `default_factory` / `collect_all` / `logger` (`compose.py:32-54`; `tests/test_compose_hooks.py:89-188`; `tests/test_falsy_defaults.py:120-138`). |
| Async hooks | Locked: no loop TypeError names helper; running loop nest-safe; no `asyncio.run` in `__set__`; coroutine objects follow the same run rules (`async_bridge.py:44-65`; `tests/test_async_callables.py`). |
| Bag keying | Locked `f"{cls.__module__}.{cls.__qualname__}"` (`hooks.py:30-32,102-109`; `tests/test_hooks_namespace.py`). |
| Generics `is_instance_of` | Locked origin+args, TypedDict fail-closed, Callable origin only, Generic subclass params not inspected (`leaves.py:30-92`; `tests/test_generics_honesty.py`). |
| `collect_all` | Locked fail-fast default and AllOf/AnyOf aggregation (`errors.py:27-40`; `tests/test_collect_all.py`). **Hole A5:** named extra checks sit outside that bag. |
| `ValidationPath` | Locked unique units, aggregate owns min/max/eq leaves, unknown → `ValueError` (`path.py:33-76`; `tests/test_path_fail_closed.py`). |
| Named-once leaves | Locked: Payment/Aadhaar/PAN/Expiry bags do not grow (`tests/test_named_validate_once.py`). |
| Aadhaar / PAN / Pattern atoms | Locked identity ∩ checksum; Digit/Word compose on findall (`tests/test_aadhaar_card.py`, `test_pan_card.py`, `test_pattern_findall.py`). **Holes A2–A4** on the Pattern algebra / bytes path. |
| Rejector / parity leftovers | None still real (B11). |

---

## 6. Product tip HOLD

Phase B (P1 fixes + expanded unit / feature / property / lightweight load
tests) is **not** started on a mergeable product PR.

- This PR: draft research-only, KEEP-HEAD.
- Product tip: HOLD until Council CLEAR on this pack.
- Do not squash-merge. Do not undraft this pack into a product merge.
- Packs #10 / #12 / #13 / #16 remain off `main`.
- valio untouched at `3415c03`.
