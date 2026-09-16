# Soft 11 CARTGRAPH — holes / architecture / valio parity (evidence pack)

**CARTGRAPH ONLY.** No product tip. No implementation. Soft-patch valio is **read-only**.

Council can ACCEPT Soft LOCK Soft 11 from this pack alone.

---

## Identity

| Item | Value |
| --- | --- |
| Target | [`bitplorer/ux-valio`](https://github.com/bitplorer/ux-valio) `main` |
| `git log -1` HEAD | **`8c37d7fb4c1813b5dca468f582c15c1e3b9157ef`** |
| Subject | `Soft 10: origin+args type door; fail-closed unknown (#11)` |
| Soft 10 PR tip SHA | **`97e79f521d7a0ffb5b39d2b8b1228f8c5b7d7761`** ([PR #11](https://github.com/bitplorer/ux-valio/pull/11) `headRefOid`) |
| Soft 10 claimed merge | **`8c37d7f`** — **verified equal to HEAD** (`mergeCommit` of PR #11) |
| Remote `origin/main` | same SHA after `git fetch origin main` |
| Frozen valio | [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4) `3415c03e37085adda4040671a91eb19aa4fe4ac4` |
| Valio subject | `Soft 10: compose full validation path; fail-closed units (#10)` — **PARKED; not edited** |
| Experiment Python | 3.12.3 |
| Package floor | `requires-python = ">=3.10"` (`pyproject.toml` L11) |
| Suite at HEAD | **229 passed** in 0.22s, 20 files (`python3 -m pytest tests`) |

HEAD check (this run):

```
8c37d7f Soft 10: origin+args type door; fail-closed unknown (#11)
8c37d7fb4c1813b5dca468f582c15c1e3b9157ef
```

Human ask (Hinglish summary): Work. First find holes, bugs, residuals, gaps. Optimize for performance. Make design/architecture crystal-clear and clean; look for organization improvements. Then check feature parity: every meaningful valio feature must be COVERED in ux-valio or named KEEP/RETIRE/DEFER with evidence. Extra ux-valio features may stay.

Name honesty: this pack is the Soft 11 vehicle. Soft 6 forbids `docs/soft*.md` on product `main` (`tests/test_product_surface.py` L94–96). **Do not merge this draft onto `main` as a product commit.**

---

## 1. Pass A — holes / bugs / residuals / gaps (HEAD `8c37d7f`)

**P0 count: 0.** Spine Soft 1–10 still locks. New work is P1 honesty cliffs + P2 residuals.

### 1.1 HEALTHY (do not reopen Soft 1–10)

| Area | Evidence |
| --- | --- |
| Door A only; no Field/Schema/Cap | `ux_valio/__init__.py` L3–6; `README.md` L30–31; `hasattr(ux_valio, "Field")` False |
| No `add_pre_set` / no `_processors["pre_set"]` | `hooks.py` L17–27; `tests/test_door_a_honesty.py` L13–27; `tests/test_async_callables.py` L20–26 |
| `pre_set` hook **is** the validate pipeline | `base.py` L24–28; `descriptor.py` L17–19 |
| No `asyncio.run` in `__set__` | `descriptor.py` L179–187; `tests/test_async_callables.py` L29–33 |
| Async: nest-safe bridge; no loop → named `TypeError` | `async_bridge.py` L18–61; `tests/test_async_callables.py` L62–75 |
| `enable_async` unknown-kwarg `TypeError` | `tests/test_hooks_namespace.py` L319–323 |
| `cache_task` kwarg KEEP; cache behavior RETIRE | `facade.py` L56–57, `hooks.py` L92–93; `tests/test_hooks_namespace.py` L326–346 |
| debug-swallow KEEP; `collect_all` default False, not debug | `descriptor.py` L7–11, L136–145; `tests/test_collect_all.py` |
| Falsy `0` / `False` / `""` not replaced by `default` | `descriptor.py` L181–182; `tests/test_falsy_defaults.py` |
| Bound honesty `None` ≠ `0` | `bounds.py` L1–11; `tests/test_bound_honesty.py` |
| Logger default OFF | `descriptor.py` L108; `Validator().logger is False` |
| Pattern `findall` substring KEEP | `leaves.py` L164; `tests/test_pattern_findall.py` |
| PaymentCard brand ∩ Luhn; Luhn-only rejected | `payment.py` L37–50; `tests/test_payment_card.py` L24–28 |
| Named facades: extra check in `validate()`, bags do not grow | `payment.py` L57–59, `expiry.py` L75–77; `tests/test_named_validate_once.py` |
| `expire_*` only on `ExpiryValidator`; exclusive bounds | `expiry.py` L40–48; `tests/test_expiry_validator.py` L36–48, L45–48; `tests/test_door_a_honesty.py` L142–145 |
| No `expiry` path unit | `path.py` L21–30; `tests/test_expiry_validator.py` L51–52 |
| Facades do not MI concern leaves; `&` / `|` object compose | `compose.py` L1–7; `tests/test_compose_not_inherit.py` |
| `Chain is AllOf` | `compose.py` L198; `tests/test_validator_compose.py` L58–64 |
| Compose-root `add_*`; leaves bag-free | `tests/test_compose_hooks.py` L20–28 |
| Compose conflicting **specified** `debug` / `default` → `TypeError` | `compose.py` L32–46; `tests/test_compose_hooks.py` L101–119 |
| Hook bags `module.qualname`; free fn needs `namespace=` | `hooks.py` L30–67; `tests/test_hooks_namespace.py` |
| Processors then tasks once | `hooks.py` L112–115; `tests/test_processors_then_tasks.py` L29–41 |
| Get/delete hooks receive **name**, not stored value (KEEP) | `descriptor.py` L20–21, L193–207; `tests/test_processors_then_tasks.py` L120–136 |
| Soft 10 `is_instance_of`: origin+args, Annotated, Literal, NewType, Union, TypeError→False | `leaves.py` L30–85; `tests/test_generics_honesty.py` |
| Soft 2 bind: Union / `list`↔`List` agree; conflict fail-closed | `descriptor.py` L44–63, L163–177; `tests/test_annotation_conflict.py` |
| Path **init** fail-closed (duplicate / aggregate clash) | `path.py` L36–48; `tests/test_path_fail_closed.py` L10–21 |
| `__all__` barrel honesty; no Soft ceremony tokens; no pyparsing | `tests/test_product_surface.py` L26–36, L77–101 |
| `HexColorValidator` / `AttributeValidator` not public | `tests/test_product_surface.py` L71–74; `tests/test_typed_facades.py` L181–183 |
| TypedDict fail-closed (schema HOLD) | measured: `get_origin(TD) is None`; `is_instance_of({"a": 1}, TD) is False` |
| Runtime-checkable Protocol via `isinstance`; non-runtime False | measured |
| Callable origin only; signature DEFER | `leaves.py` L74–75; `tests/test_generics_honesty.py` L282–286 |
| Generic subclass instance params DEFER | `tests/test_generics_honesty.py` L289–298 |

### 1.2 P1 holes (measured)

#### CART11-A1 — P1 — postponed / string owner annotation poisons `Validator()`

**Paths:** `descriptor.py` L163–168 (owner wins when validator annotation is `None`); `leaves.py` L39–40 (`isinstance(annotation, str) → False`); `leaves.py` L125–127 (error interpolates the string).

Soft 10 already fail-closes **membership** for string annotations (`tests/test_generics_honesty.py` L236–244). Soft 2 already fail-closes **typed facades** against postponed owner `'int'` (`tests/test_door_a_honesty.py` L153–168). The leftover is `Validator()` (annotation unset): `__set_name__` **copies** the unresolved string into the type door, then every non-`None` assignment fails membership.

**Repro** (Python 3.12.3, HEAD `8c37d7f`):

```python
from __future__ import annotations
from dataclasses import dataclass
from ux_valio import Validator
field = Validator(debug=True)
@dataclass
class N:
    n: int = field
# BIND_OK annotation 'int' <class 'str'>
N(n=1)
# TypeError: n expect int type, got int type instead
```

`IntegerValidator` on the same postponed `n: int` still raises at class body (`N.n: 'int' annotation did not match IntegerValidator: int`) — locked. `debug=False` swallows and leaves the attribute unset (`None` on later read). The error text names `int` twice because `f"{annotation}"` for `'int'` has no quotes.

**Class:** hole (honesty). Not KEEP-eval: Soft 10 DEAD `eval` of postponed strings. Fix is fail-closed at **bind** for unresolved owner annotations (str / `ForwardRef`), same family as Soft 2, for every Door A descriptor.

#### CART11-A2 — P1 — AnyOf `|` is AND-gated by merged type

**Paths:** `compose.py` L89–103 (`_compose_annotation` TypeError on conflict); `compose.py` L204–210 (`AnyOf.validate` runs `TypeValidator._validate_type` **before** alternatives); `base.py` L80–85 (`__or__` → `AnyOf`).

Taught OR is `A | B`. Measured:

| Expression | Result |
| --- | --- |
| `IntegerValidator(debug=True) \| StringValidator(debug=True)` | `TypeError: composed validators have conflicting annotations: <class 'int'> vs <class 'str'>` |
| `IntegerValidator(debug=True) \| Validator(debug=True)` | compose succeeds, annotation `int` |
| then `box.x = "a"` (no owner annotation) | `TypeError: x expect <class 'int'> type, got str type instead` — String/untyped alternative never runs |
| `PatternValidator(r"cat") \| PatternValidator(r"dog")` | **WORKS** (no member annotations) — `tests/test_validator_compose.py` L86–97 |

`AllOf` of conflicting typed facades **should** fail-closed (`tests/test_validator_compose.py` L135–137). AnyOf of conflicting types is the actual `|` use. Root type-check is an AND in front of OR.

**Class:** hole (compose algebra honesty). Not a new public name: stop AND-gating AnyOf; leave member `validate()` as the OR. AllOf annotation conflict stays TypeError.

#### CART11-A3 — P1 — compose merge treats `collect_all=False` / `logger=False` as unspecified

**Paths:** `compose.py` L32–46, L78–86. `_merged_attr(..., unspecified=False)` skips members whose value **is** `False`, so explicit `False` never enters conflict detection.

**Repro:**

```
LengthValidator(min_length=1, collect_all=True) & RequiredValidator(required=True, collect_all=False)
→ collect_all True   # no TypeError
LengthValidator(min_length=1, logger=True) & RequiredValidator(required=True, logger=False)
→ logger True        # no TypeError
LengthValidator(min_length=1, debug=True) & RequiredValidator(required=True, debug=False)
→ TypeError conflicting debug   # KEEP, uses unspecified=None
```

Caveat: `Property.__init__` always sets `collect_all=False` and `logger=False` (`descriptor.py` L82, L108). Default-False vs explicit-True **should** keep True (unspecified collapse). The hole is **explicit** False vs True, which debug can see because debug’s unspecified sentinel is `None`. Locks only cover `debug` / `default` (`tests/test_compose_hooks.py` L101–119). `doc` uses `None` and **does** TypeError on `'a'` vs `'b'` (measured).

**Class:** hole. Fix needs a specified-sentinel without changing runtime default `collect_all=False`.

#### CART11-A4 — P1 — `ValidationPath.run` unknown unit is bare `KeyError`

**Path:** `path.py` L62–67 `lookup[name](...)`. Init is fail-closed (`path.py` L36–48). Run of a missing key is not.

**Repro:**

```
ValidationPath(('type',)).run(None, None, 1, {})
→ KeyError 'type'
class Bad(Validator):
    validation_path = ValidationPath(('nonexistent',))
Bad(debug=True).validate(None, 1)
→ KeyError 'nonexistent'
ValidationPath(('type',)).run(..., lookup={}, collect_all=True)
→ ValidationErrors wrapping KeyError 'type'
```

User-facing Door A never sets `validation_path`. The story “path fail-closed” is incomplete for extenders. Double-call already raises `ValueError` (`path.py` L64).

**Class:** hole (fail-closed residual). Same door: `ValueError(f"validation path unknown unit: {name!r}")`.

### 1.3 P2 residuals

#### CART11-B1 — P2 — `cache_task` on compose roots

`Validator` accepts `cache_task` (`facade.py` L56–77). `AllOf.__init__` calls `_init_hook_bags()` with default `True` then `Property.__init__(**kwargs)` (`compose.py` L111–117). `AllOf(..., cache_task=False)` → `TypeError: Property.__init__() got an unexpected keyword argument 'cache_task'`. AGENTS: kwarg KEEP, behavior RETIRE. API cliff, not a second cache door.

#### CART11-B2 — P2 — UUID/Path coerce lives in `pre_validation_processing`, not `validate()`

Descriptor path: `base.py` L24–28 runs coerce then `validate()`. Direct `UUIDValidator.validate(None, "<uuid-str>")` → `TypeError` expect UUID, got str. Assignment of the same string stores a `uuid.UUID` (`typed.py` L58–64, `tests/test_typed_facades.py` L86–94). Same split for `PathValidator` (`typed.py` L78–81). One door (descriptor); function-validate is a second call shape, not a second product door. Honesty cliff for callers of `.validate()`.

#### CART11-B3 — P2 — `ReassignValidator` / facade `_assignment_counts` keyed by `id(obj)` never drop

`leaves.py` L180–188, `facade.py` L70–92. After `del o; gc.collect()`, the id remains (measured). Rotting lock / unbounded dict. Delete hooks do not pop.

#### CART11-B4 — P2 — `__get__` on never-set attribute with `debug=True` re-raises `KeyError`

`descriptor.py` L189–197. `G.__new__(G); g.s` → `KeyError 's'`. `debug=False` returns `None` (KEEP swallow). Residual UX, not a dual door.

#### CART11-B5 — P2 — PEP 695 `type IntList = list[int]` is fail-closed unknown

`get_origin(IntList) is None`; `IntList.__value__` is `list[int]`; `is_instance_of([1], IntList) is False` (3.12.3). Soft 10 fail-closed unknown. Floor stays 3.10. Unwrap `__value__` would be the same helper, not typingx.

#### CART11-B6 — P2 — `IntegerValidator` vs `int \| None` / postponed typed facades (KEEP fail-closed, thin docs)

`tests/test_annotation_conflict.py` L96–100; `tests/test_door_a_honesty.py` L153–168. README does not warn. Use `Validator()` for optional/union fields, or drop the typed facade. Related to A1: `Validator()` + postponed is currently worse than a typed facade (silent copy then reject).

#### CART11-B7 — P2 — `expire_on` is nanosecond equality (valio parity)

`expiry.py` L88–89 `expired = now == parsed`. Date-only `"2020-01-01"` becomes midnight; `datetime.now() == that` is almost never True. Assignment succeeds (measured). Valio@3415c03 `validators.py` L1335–1336 is the same `now == expiry`. **KEEP as frozen-valio parity**, not a ux-only hole.

#### CART11-B8 — P2 — `bytes` is `Sequence[int]` (stdlib fact)

`is_instance_of(b"ab", Sequence[int]) is True`. Not a hole. `str` as `Sequence[str]` is True (characters). Soft 10 abc walk KEEP.

### 1.4 Dual-door / E14 temptations — do not propose

- `add_pre_set` / `_processors["pre_set"]`
- Field / Schema / Cap / `mount_channel` / `rule/` / Result
- Public `check_instance` / export `is_instance_of`
- `enable_async` flag; `asyncio.run` in `__set__`
- `eval` / `get_type_hints` of postponed strings (Soft 10 DEAD)
- `ListValidator` / Phone / collection facades
- `HexColorValidator` / `AttributeValidator` / RGB/HSL
- Dual-schema `INT = Union[int, Validator]`

---

## 2. Pass B — architecture / clarity / organization / performance

### 2.1 One door, three stacking mechanisms

Door A is one caller shape: `field: T = SomeValidator(...)`. Inside that door, checks stack three ways:

| Mechanism | Owner | What it is |
| --- | --- | --- |
| Ordered path units | `Validator.validation_path` + `_unit_lookup` (`path.py` L21–30, `facade.py` L94–118) | Fat facade: reassignment → type → required → pattern → multiple_of → length → value → choice |
| Object compose | `ValidateProperty.__and__` / `__or__` → `AllOf` / `AnyOf` (`base.py` L73–85, `compose.py`) | One descriptor; members `validate()`; `Chain is AllOf` |
| Hook bags | `HookHost` on `Validator` and compose **root** only (`hooks.py`) | `add_pre_validator` / `add_validator` / `add_*_task`; no `pre_set` bag |

These are not dual doors. They **are** three degrees of freedom. Crystal-clear teaching: hang `add_*` on the field default (facade or compose root); concern leaves stay bag-free; `&` is AllOf; `|` is AnyOf (A2 currently lies).

`pre_set` hook = validate pipeline. `add_pre_set` would be a second door. KEEP absent.

### 2.2 Module ownership (no rename pass)

| Module | Owns |
| --- | --- |
| `ux_valio/descriptor.py` (213) | `Property` lifecycle, annotation identity, debug-swallow, `collect_all` |
| `ux_valio/pattern.py` (126) | `Pattern` / `PatternType` / `WordBoundary` combinators (`&` concat, `\|` alt) |
| `validators/base.py` (89) | `ValidateProperty` ABC; `&` / `\|` |
| `validators/hooks.py` (205) | `HookHost` bags; `module.qualname` keys |
| `validators/path.py` (72) | `ValidationPath`; not in package `__all__` |
| `validators/facade.py` (130) | `Validator` + `Integer` / `String` / `Boolean` |
| `validators/leaves.py` (251) | Type/required/pattern/reassign/multiple/choice + unexported `is_instance_of` |
| `validators/length.py` / `value.py` / `bounds.py` | Leaf-owned bounds; `None` ≠ `0` |
| `validators/compose.py` (232) | `AllOf` / `AnyOf` / `Chain` |
| `validators/typed.py` (163) | Remaining typed facades (no RGB/HSL/HexColor) |
| `validators/payment.py` / `expiry.py` | Soft 8 facades; extra check in `validate()` |
| `validators/async_bridge.py` | Nest-safe worker; no `asyncio.run` in setter |
| `validators/errors.py` | `ValidationErrors`; `continue_or_raise` |

`is_instance_of` lives next to `TypeValidator` — one type door, two callers (descriptor path unit `"type"` and compose-root `TypeValidator._validate_type`). Do not mint a public `check_*`. Integer/String/Boolean sitting in `facade.py` vs the rest in `typed.py` is historical, not a second concept. **No aesthetic move.**

`bound()` (`bounds.py` L24–26) is `return value if value is not None else None` after `getattr(..., None)` — identity wrapper. Clarity residual, not a Soft DO (no L gain).

### 2.3 Barrel honesty

| Surface | Count | Evidence |
| --- | --- | --- |
| `from ux_valio import *` | **40** names | measured; `__all__` has 41 including `__version__` (`ux_valio/__init__.py` L52–94) |
| `validators.__all__` ⊂ package `__all__` | lock | `tests/test_product_surface.py` L99–101 |
| `from valio import *` @ 3415c03 | **306** names | measured this run with typingx/pyparsing/phonenumbers; valio has **no** `__all__` (`valio/__init__.py` L7–14 star-imports 7 packages) |
| Path / async-bridge names | not in `__all__` | KEEP |

Valio barrel includes control-char `Pattern`s, URI ABNF, `Field` / `Schema`, `StartOfString`, `HexColorValidator`, `PhoneNumberValidator`, `cancel`. ux-valio does not pretend to re-export that. Extra ux names (`AllOf`, `AnyOf`, `ValidationErrors`, `EmailValidator`, `IPv4Validator`, public Min/Max leaves) stay.

### 2.4 Hot paths — measured costs; Soft DO only if L conserved

| Path | Cost at HEAD | Soft DO? |
| --- | --- | --- |
| `is_instance_of` nested `list[list[int]]` | 200 walks of 200×20 ints: **0.536s**; fail-fast wrong element: **0.0006s** | **No.** O(n) fail-fast is the algorithm. Memoizing origin/args is fashion overlay (E14). Empty containers already True (`leaves.py` L96–97). |
| Hook bag lookup `_bag_key` | 100k: **0.0087s** | **No.** String format per phase is noise vs user validators. |
| `PatternValidator` `re.compile` every call | 5000 validates: **0.0024s** | **No.** Compile cache would be a new private map for no L. |
| Nest-safe bridge | new loop + `ThreadPoolExecutor` **per async callable** (`async_bridge.py` L40–41) | **No this Soft.** Real cost if someone hangs async on a hot setter; KEEP nest-safe vs `asyncio.run` in `__set__`. Worker reuse would be a later Soft with a measured L, not ceremony. |
| AllOf double type | compose root `TypeValidator` then member `IntegerValidator.validate` path includes `"type"` again | **No.** Cheap. A2 is the AnyOf AND-gate, not this. |

Crystal-clear = one name per concept. `Chain` = `AllOf` is taught alias, not a third AND. `collect_all` is not `debug`. `pre_set` hook is not a processor bag named `pre_set`.

---

## 3. Pass C — feature parity valio@3415c03 → ux-valio HEAD `8c37d7f`

Legend: **COVERED** analogue on Door A · **PARTIAL** same name/role, different contract · **MISSING** no analogue · **RETIRED-named** AGENTS/README/tests name the absence · **DEFER** named out · **HOLD** council park · **EXTRA** ux-only (may stay).

Soft column: ux Soft that shipped the analogue, if any.

### 3.1 Core descriptor / errors / logger / defaults

| valio capability | valio evidence | ux-valio | Soft |
| --- | --- | --- | --- |
| `Property` descriptor | `descriptor/descriptors.py` L31 | COVERED `descriptor.py` L72 | 1 |
| Falsy `0`/`False`/`""` keep assigned | `descriptors.py` L262–263 | COVERED `descriptor.py` L181–182 | 1 |
| `debug` re-raise vs swallow | `descriptors.py` L273–274 | COVERED `descriptor.py` L136–145 | 1 |
| Annotation bind fail-closed | `descriptors.py` L157–202 `issubclassx` | COVERED stdlib identity, **not** issubclassx `descriptor.py` L44–63, L163–177 | 2 |
| Logger mixin default on | `logger/loggers.py` L14–28; barrel `Logger` | RETIRED-named logger default **OFF** `descriptor.py` L24, L108 | 1 |
| `Set/Get/DeletePropertyError`, `DustError` | `error/errors.py` L8–106 | RETIRED-named → `errors` list + `ValidationErrors` | 7 (`ValidationErrors`) |
| `collect_all` | **absent** (grep) | EXTRA `descriptor.py` L9–11 default False | 7 |
| `enable_async` | `validators.py` L1698, L1626 | RETIRED-named unknown-kwarg | 5 |
| `allow_validation` | `validators.py` L1699 | RETIRED (no analogue; not taught) | — |
| `cache_task` kwarg + `_job` cache | `validators.py` L1625, L1489–1500 | PARTIAL: kwarg KEEP, cache RETIRE | 5 |
| `asyncio.run` in processing | `validators.py` L807–811, L1803–1804 | RETIRED-named nest-safe bridge | 5 |

### 3.2 Concern leaves / path / compose

| valio capability | valio evidence | ux-valio | Soft |
| --- | --- | --- | --- |
| `TypeValidator` + typingx `isinstancex` | `validators.py` L359, L65 | COVERED unexported `is_instance_of` stdlib origin+args | 10 |
| `RequiredValidator` | L417 | COVERED | 1 |
| `PatternValidator` `findall` | L461, L489–512 | COVERED `leaves.py` L156–164 | 1 |
| `ReassignValidator` | L516 | COVERED | 1 |
| `MultipleValidator` | L570 | COVERED | 1 |
| `Min/MaxValueValidator` | L868, L915 — **not** in valio `validators.__all__` | COVERED **and exported** | 6 |
| `ValueValidator` | L984 | COVERED | 1 |
| `Min/MaxLengthValidator` | L1076, L1124 — not in valio barrel | COVERED **and exported** | 6 |
| `LengthValidator` | L1173 | COVERED | 1 |
| `ChoiceValidator` | L1347 | COVERED | 1 |
| `ExpiryValidator` leaf + `expire_*` on fat `Validator` + path unit `"expiry"` | L1265–1344; L1688–1709; L1639 | PARTIAL → RETIRED-named path/kwargs on `Validator`; COVERED as **facade only** `expiry.py` | 8 |
| `AttributeValidator` | L1432–1472; path `"attribute"` L1641 — **not** in `validators.__all__` / star barrel | RETIRED-named not shipped | 6 |
| `TaskValidator` class | L1476–1577 barrel | RETIRED-named; hook bags only | 5 |
| `_ValidationPath` private | L820, L1631–1642 includes expiry+attribute | COVERED private `ValidationPath`; default names omit expiry/attribute `path.py` L21–30 | 6 |
| Validator `&` / `\|` / `AllOf` / `AnyOf` / `Chain` | **No** (historical MI retired to path) | EXTRA object compose | 6–7 |
| Pattern `&` / `\|` | `regexps.py` L57–72 | COVERED `pattern.py` L39–46 | 1 |

### 3.3 Typed / domain facades

| valio capability | valio evidence | ux-valio | Soft |
| --- | --- | --- | --- |
| `IntegerValidator` / `Float` / `Decimal` / `Boolean` / `Bytes` / `String` | L1971–2006 | COVERED | 1 / 6 |
| `HexShort/Long/Color`, `RGBOrRGBA`, `HSLOrHSLA` | L2030–2075 **in barrel** | RETIRED-named; `HexColorValidator` not public | 6 / AGENTS |
| `DateValidator` eu/ind **string** patterns | L2087–2149 pyparsing dates | PARTIAL: `datetime.date` only, strings rejected `typed.py` L44–47; `tests/test_typed_facades.py` L65–73 | 6 |
| `Enum` / `StringEnum` / `IntegerEnum` | L2152–2160 | COVERED `typed.py` L131–163 | 6 |
| `UUIDValidator` | L2164 annotation only | COVERED + EXTRA string coerce on descriptor path `typed.py` L55–64 | 6 |
| `EmailIDValidator` | L2169 | COVERED as `EmailValidator` (rename) `typed.py` L50–52; findall KEEP | 6 |
| `PaymentCardValidator` brand ∩ Luhn | L2194–2226; relib pyparsing | COVERED stdlib `re` `payment.py`; Luhn-only rejected | 8 |
| `PhoneNumberValidator` | L2230–2265 `phonenumbers` | **DEFER** — `hasattr` False; README L173 | 6 named |
| `PathValidator` | L2268–2308 `StringValidator`, always path-exists-ish | PARTIAL: annotation `pathlib.Path`, coerce str, `path_exists=` opt-in `typed.py` L67–89 | 6 |
| `IP4/IP6/IPAny` | L2311–2356 | COVERED as `IPv4Validator` / `IPv6Validator` / `IPAddressValidator` | 6 |
| `AadhaarCardValidator` / `PANCardValidator` | L2360, L2392 | **DEFER** (India-id leaves; no analogue; not in README DEFER list — pack names them with Phone) | — |
| `Mapping/Sequence/List/Dictionary/Set/TupleValidator` | L2424–2444 **in barrel** | **DEFER** collections `tests/test_product_surface.py` L48–49 | 6 / 10 |

Soft 8 deferred PaymentCard / Expiry / named-once — **still true as landed**, not still deferred:

| Claim | HEAD evidence |
| --- | --- |
| PaymentCard brand ∩ Luhn | `payment.py` L41–50; `tests/test_payment_card.py` L20–28 |
| Expiry exclusive `expire_*` on facade; not on `Validator`; no path unit | `expiry.py` L40–48, L62–77; `tests/test_expiry_validator.py` |
| Named-once: `validate()` extra check, bags do not grow | `tests/test_named_validate_once.py` L13–38 |

### 3.4 Processors / tasks / async

| Phase | valio@3415c03 | ux-valio HEAD | Status |
| --- | --- | --- | --- |
| pre_set **hook** = pre_val → validate → post_val | `validators.py` L182–194 | `base.py` L24–28 | COVERED |
| pre_set **processor bag** | none | none (`hooks.py` L17–19) | KEEP absent |
| `add_pre_validator` / post / post_set / get / delete | L1850–1953 | `hooks.py` L151–177 | COVERED |
| `add_validator` custom | L1828–1833 | `hooks.py` L98–100, L138–149 | COVERED |
| tasks after processors | L807–811 `asyncio.run` | `hooks.py` L112–115 nest-safe | COVERED (async shape changed Soft 5) |
| get/delete value honesty | descriptor passes name-like | KEEP name, not stored value `descriptor.py` L193–207 | COVERED / KEEP |

### 3.5 Field / Schema / typingx / pyparsing / compose #30

| Item | valio evidence | ux-valio | Status |
| --- | --- | --- | --- |
| Field twin (`Field`, `*Field`) | `field/fields.py` L191, L245–985; barrel | absent | **HOLD** dual-schema |
| Schema twin v2 `Schema(fields.Field)` | `schema/__init__.py` L8–9 exports `schemas_v2.py` L21; v1 `schemas.py` **commented out** of package export | absent | **HOLD** dual-schema |
| Dual-schema `Union[T, Validator]` aliases | `validators.py` L329–355 `INT`, `STR`, … | not invented; Soft 2 tests say HOLD `tests/test_annotation_conflict.py` L10–11 | **HOLD** |
| typingx | `pyproject.toml`; `isinstancex` L65; `issubclassx` descriptors L174 | stdlib `get_origin`/`get_args` only | **HOLD** / retired on Door A |
| pyparsing | `pyproject.toml`; relib emails/dates/paymentcards | product tree import lock `tests/test_product_surface.py` L77–91 | **HOLD** |
| compose #30 (regexer combinator stack) | `regexer/regexps.py` `__all__` L12–34: `All`, `SetOf`, `CapturingGroup`, `StartOfString`, lookarounds, … + `relib/*` star into 306-name barrel. Soft 6 PR named “Dual-schema / typingx / pyparsing / compose #30” DEFER. | public Pattern subset: `Pattern`, `PatternType`, `WordBoundary` only | **HOLD** — Pattern `&`/`\|` KEEP; the rest of regexer stays parked |
| Phone / collections | barrel + README | README L173; product-surface lock | **DEFER** — confirm |

### 3.6 Star-import barrel size honesty

| | valio@3415c03 | ux-valio HEAD |
| --- | ---: | ---: |
| `from … import *` | **306** (no `__all__`) | **40** (explicit `__all__`, 41 with `__version__`) |
| `AllOf` in star | False | True |
| `Field` / `Schema` | True | False |
| `AttributeValidator` | False (class exists, not exported) | False (not shipped) |
| `MinValueValidator` | False (class exists, not exported) | True (public building block) |

### 3.7 Extra ux-valio (may stay)

`collect_all`, `AllOf`/`AnyOf`/`Chain`, `ValidationErrors`, nest-safe async, public Min/Max leaves, `EmailValidator` name, `IPv4Validator` names, UUID string coerce, `Path` as `pathlib.Path`, PaymentCard via stdlib `re`, `module.qualname` bags, Soft 10 origin+args type door.

---

## 4. Soft LOCK Soft 11 (ACCEPT text)

Harden **existing** doors. No E14 new public names. No Cap / `add_pre_set` / Field / Schema / typingx / pyparsing / public `check_instance`. No product Soft tip in the cartograph run. Soft-patch valio stays PARKED @ `3415c03`. KEEP Soft 1–10.

Intent filter for every DO: **parity honesty OR hole close OR clarity without L drop**. Prefer sentinel/bind/AnyOf-skip over new types.

### 4.1 DO

| ID | Change | Intent | Door (existing) |
| --- | --- | --- | --- |
| **DO-1** | Unresolved owner annotation (`str` / `ForwardRef`) → `TypeError` at `__set_name__`. Do **not** copy into the type door. Do **not** `eval` / `get_type_hints`. | Hole close A1; same family as Soft 2 typed-facade conflict | `_bind_owner_annotation` |
| **DO-2** | `AnyOf`: do **not** AND-run `TypeValidator._validate_type` on the compose root before alternatives; do **not** TypeError on conflicting member annotations (leave compose annotation unset). `AllOf` keeps annotation-conflict `TypeError`. | Hole close A2; taught `\|` is OR | `AnyOf.validate`, `_compose_annotation` |
| **DO-3** | Compose merge: specified-sentinel for `collect_all` / `logger` so explicit `False` vs `True` is `TypeError`. Runtime default stays `collect_all=False` / logger OFF. Default-False vs explicit-True still keeps True. | Hole close A3; match `debug`/`default`/`doc` honesty | `_merged_attr` / bind kwargs |
| **DO-4** | `ValidationPath.run` missing lookup key → `ValueError` (same family as double-call), not `KeyError`. | Hole close A4; path fail-closed | `path.py` `run` |

P2, same Soft if cheap (still existing doors):

| ID | Change | Intent |
| --- | --- | --- |
| **DO-5** | `is_instance_of`: unwrap PEP 695 `TypeAliasType.__value__` when present (`getattr`, floor 3.10). Recurse. Unknown still False. | Soft 10 leftover hole close B5; not typingx |
| **DO-6** | Accept `cache_task=` on `AllOf`/`AnyOf` and pass to `_init_hook_bags`. Cache behavior still RETIRE. | A3’s cousin B1; kwarg KEEP symmetry |
| **DO-7** | Drop reassignment counts on `__delete__` (or `WeakKeyDictionary`). | Rotting lock B3 |

**Not DO this Soft:** Pattern compile cache, `is_instance_of` memo, nest-safe worker pool, moving Integer/String/Boolean into `typed.py`, deleting `bound()`, `expire_on` date-granularity (valio parity KEEP), collection facades, Phone, Date string eu/ind parse (PARTIAL is product choice).

### 4.2 KEEP

- Soft 1 Door A bones; no `asyncio.run` in `__set__`; falsy defaults; debug-swallow; logger OFF; Pattern `findall`
- Soft 2 annotation conflict (not issubclassx); postponed **typed facade** class-body TypeError
- Soft 3 no `add_pre_set`
- Soft 5 async register + nest-safe bridge; `enable_async` unknown-kwarg; `cache_task` kwarg / cache RETIRE
- Soft 6 validators package; leaf-owned length/value; object compose; ceremony strip; `docs/soft*.md` not on product main
- Soft 7 compose-root hooks; `collect_all` default False; `Chain is AllOf`; `debug`/`default` merge fail-closed
- Soft 8 PaymentCard brand∩Luhn; Expiry exclusive facade; named-once `validate()` extra check
- Soft 9 `module.qualname` bags; free function requires `namespace=`; class-object keys rejected
- Soft 10 origin+args `is_instance_of`; TypeError→False; Annotated/NewType/Literal; Callable signature DEFER; Generic instance params DEFER; TypedDict False; no public `check_instance`
- Get/delete hooks see **name**; only `pre_set` hook return is stored
- Bool-as-int; None-skip on `_validate_type`; Python ≥ 3.10
- Soft-patch valio PARKED @ `3415c03`

### 4.3 DEAD

- Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`, Result type
- `add_pre_set` / `_processors["pre_set"]`
- typingx / typing_extensions on the type door
- Public `check_instance` / `check_*` owned API
- `eval` of postponed strings
- Dual-schema `INT = Union[int, Validator]`
- RGB/HSL facades; public `HexColorValidator`
- `AttributeValidator` shipped class
- Star-import 306-name barrel
- `enable_async` as a door
- Soft ceremony tokens on product tree (`Soft LOCK` / `Soft DO` / …)

### 4.4 DO NOT

- Product Soft tip in this cartograph run; land this pack on `main`
- Soft-patch valio
- Phone / `ListValidator` / collection facades (DEFER)
- Raise Python floor
- New public compose algebra names (E14)
- Worker-pool async fashion; `is_instance_of` cache fashion
- Reopen Soft 10 “parametrized args stay permissive” (already RETIRED)

### 4.5 DEFER / HOLD (confirm)

| Item | Status | Evidence |
| --- | --- | --- |
| Phone | **DEFER** | valio L2230; ux `hasattr` False; README L173 |
| Collections (`List`/`Dict`/`Set`/`Tuple`/`Mapping`/`Sequence` Validator) | **DEFER** | valio L2424–2444; `tests/test_product_surface.py` L48–49 |
| Aadhaar / PAN | **DEFER** (named here; same bucket as Phone) | valio L2360, L2392; no ux analogue |
| Callable signature checking | **DEFER** | Soft 10 lock; `tests/test_generics_honesty.py` L282–286 |
| Generic subclass instance params (`Box[int]` vs `Box("a")`) | **DEFER** | Soft 10 lock; L289–298 |
| Field / Schema dual-schema | **HOLD** | valio field + `schemas_v2.py` L21; ux `__init__.py` L4–5 |
| typingx | **HOLD** | valio `isinstancex` L65 |
| pyparsing + compose #30 regexer stack | **HOLD** | valio `regexer/`; Soft 6 PR DEFER line; ux Pattern subset only |
| Date eu/ind string facade | not DEFER — **PARTIAL KEEP** product (`datetime.date`, no parse) | `typed.py` L44–47 |

---

## 5. Risks if Council ACCEPTS this lock

- **DO-1 × PEP 563:** modules with `from __future__ import annotations` cannot use Door A until they drop postponed annotations or (later Soft) resolve types. That is the honesty trade: today `Validator()` already rejects real ints with a lying message. Fail-closed at class body is louder and consistent with `IntegerValidator`.
- **DO-2 × owner annotation:** `n: int \| str = IntegerValidator() \| StringValidator()` should bind. AllOf of those two must still TypeError.
- **DO-3 specified-sentinel:** must not break `LengthValidator(collect_all=True) & RequiredValidator()` (unspecified False → keep True). Tests must name **explicit** False vs True.
- **DO-5 PEP 695:** 3.10 has no `TypeAliasType`; `getattr(__value__)` is enough. Do not import `typing_extensions`.
- Soft 6 lock: implementing Soft 11 later must **not** land this pack on product `main`.

---

## 6. This PR vs Soft 6

`tests/test_product_surface.py` L94–96 forbids `docs/soft*.md` on product `main`. This draft is the pack vehicle (same contract as [PR #10](https://github.com/bitplorer/ux-valio/pull/10) Soft 10 CARTGRAPH).

**Do not merge onto `main` as a product commit.** ACCEPT the lock from the pack; a later Soft implements DO-1… with no ceremony docs.

No product code in this PR.
