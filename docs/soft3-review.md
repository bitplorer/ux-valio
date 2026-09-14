# Soft 3 review — Door A vs valio@3415c03

Frozen reference: [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
Soft 2 tip: `14743f9`. Soft-patch valio is **untouched**.

Council lock (Soft 3): **do not invent `_processors["pre_set"]` / `add_pre_set`.**
That would be dual-door E14. valio bags have no `pre_set` key. Descriptor
`pre_set` already owns `pre_validate → validate → post_validate`.

Public door stays `field: T = SomeValidator(...)`. No Field / Schema / Cap /
Result invented here.

---

## Leftover teaching: `pre_set` hook ≠ processor bag

Soft 1’s line **“only `pre_set` return is stored”** names the **descriptor
hook return** (`Property.__set__` stores whatever `pre_set` returned). It does
**not** name a missing `_processors["pre_set"]` bag.

| Layer | What exists | What does not |
| --- | --- | --- |
| Descriptor hooks | `pre_set` / `post_set` / `pre_get` / `post_get` / `pre_delete` / `post_delete` | — |
| `ValidateProperty.pre_set` | `pre_validation_processing` → `validate` → `post_validation_processing` | a second `pre_set` processing phase |
| `Validator` processor **bags** | `pre_validate`, `post_validate`, `post_set`, `pre_get`, `post_get`, `pre_delete`, `post_delete` | **`pre_set`** |
| `add_*` registration | `add_pre_validator`, `add_post_validator`, `add_post_set`, `add_pre_get`, `add_post_get`, `add_pre_delete`, `add_post_delete` (+ `_task` twins) | **`add_pre_set`** |

Hang “before store” work on **`add_pre_validator`** (runs inside `pre_set`,
return **is** stored). Hang “after store” work on **`add_post_set`** (return
**is not** stored — same as valio).

### Why `post_set` has a bag and `pre_set` does not (screenshot KEEP)

Soft 1 `_processors` keys (`ux_valio/validators.py` L603–616) match the
screenshot: `pre_validate`, `post_validate`, `post_set`, `pre_get`, `post_get`,
`pre_delete`, `post_delete`. **No `pre_set`.** That is not E15 (silent drop).
valio Door A has the same seven bags (`valio/validator/validators.py`
L1757–1764) and the same `add_*` list (L1860–1952). Transform-before-validate
is folded into **`pre_validate` only**, because that bag already runs *inside*
descriptor `pre_set` *before* `validate` and *before* store:

```
__set__ → pre_set hook
            → pre_validate processors  (transform; return kept)
            → validate
            → post_validate processors (transform; return kept)
        → store that return
        → post_set hook
            → post_set processors      (side effect; return ignored)
```

`post_set` needs its own bag because it is a **different lifecycle moment**
(after store). `pre_set` does not: a `_processors["pre_set"]` / `add_pre_set`
API would be a second door onto the same moment as `add_pre_validator` (E14).
Soft 3 KEEP. Behavior lock: `tests/test_soft3_honesty.py`::`test_no_add_pre_set_on_validator`.

**valio@3415c03 cites**

- Descriptor stores only `pre_set` return:
  `valio/descriptor/descriptors.py` L264–268
  (`value = self.pre_set(...)`; `obj.__dict__[self.name] = value`;
  `self.post_set(...)` ignored).
- `ValidateProperty.pre_set` **is** the validate pipeline:
  `valio/validator/validators.py` L182–192
  (`pre_validation_processing` → `validate` → `post_validation_processing`).
- Processor bags on `Validator.__init__`:
  `valio/validator/validators.py` L1757–1764 —
  `_custom_pre_validator`, `_custom_post_validator`,
  `_custom_post_set_processor`, `_custom_pre_get_processor`,
  `_custom_post_get_processor`, `_custom_pre_delete_processor`,
  `_custom_post_delete_processor`. **No `_custom_pre_set_*`.**
- Registration APIs: same file L1860–1952 (`add_pre_validator`,
  `add_post_validator`, `add_post_set`, `add_pre_get`, `add_post_get`,
  `add_pre_delete`, `add_post_delete`). **No `add_pre_set`.**
- Door B Field mirrors the same list (retired here):
  `valio/field/fields.py` L128–153.

**ux-valio cites**

- Descriptor store: `ux_valio/descriptor.py` L153–159.
- Pipeline inside `pre_set`: `ux_valio/validators.py` L77–80.
- Processor keys: `ux_valio/validators.py` L593–604
  (`pre_validate`, `post_validate`, `post_set`, `pre_get`, `post_get`,
  `pre_delete`, `post_delete`). **No `pre_set`.**
- `add_*`: `ux_valio/validators.py` L677–731. **No `add_pre_set`.**

**Verdict:** missing `pre_set` in the processors list is **intentional**, not a
hole. Soft 3 does **not** restore it.

---

## Pass 1 — Surface inventory

### `__all__` (`ux_valio/__init__.py`)

`BooleanValidator`, `ChoiceValidator`, `IntegerValidator`, `LengthValidator`,
`MultipleValidator`, `Pattern`, `PatternType`, `PatternValidator`, `Property`,
`ReassignValidator`, `RequiredValidator`, `StringValidator`, `TypeValidator`,
`ValidateProperty`, `Validator`, `ValueValidator`, `WordBoundary`,
`__version__`.

Not exported (internal compose guts): `MinValueValidator`, `MaxValueValidator`,
`MinLengthValidator`, `MaxLengthValidator`, `ValidationPath`. Soft 3 does not
add them to `__all__`.

### Door A happy paths (Soft 1 README + tests)

`field: T = SomeValidator(...)` with `StringValidator` / `IntegerValidator` /
`BooleanValidator` / `Validator` kwargs: `required`, `pattern`, `reassign`,
`multiple_of`, `min_value`/`max_value`/`gt`/`lt`/`value`/`eq`,
`min_length`/`max_length`/`length`, `in_choice`/`not_in_choice`, `default`,
`debug`, `logger`. Class `__get__` returns `None` so dataclass `__init__`
routes `Cls()` through `__set__(instance, None)` then `default`.

### Hook surface

Descriptor: six methods as above. `ValidateProperty` maps them to `*_processing`
methods. `Validator` runs **processors then tasks once** per phase. Get/delete
hooks receive `self.name`, not the stored value (valio L287 / ux-valio L167).

### Processor vs task split

Processors may rewrite `value` (return chained). Tasks run after, return
ignored. No `asyncio.run` in `__set__`. `cache_task` is still a constructor
kwarg (valio asyncio cache); ux-valio tasks always run once per phase — see
Pass 5 RETIRE.

### `ValidationPath`

Ordered unique names. Double-call and aggregate+owned-leaf fail closed. A
second `validate()` is a new pass. Default:
`reassignment, type, required, pattern, multiple_of, length, value, choice`.
valio also had `expiry` + `attribute` on this path — DEFER (Soft #6 / not Soft 1
surface).

---

## Pass 2 — Descriptor lifecycle honesty vs valio@3415c03

Focus: `Property` / `ValidateProperty` vs
`valio/descriptor/descriptors.py` and `valio/validator/validators.py`.

| Step | valio@3415c03 | ux-valio Soft 2 | Honesty |
| --- | --- | --- | --- |
| `__set_name__` name bind | L134–155: set if `None`; `AttributeError` if name differs **and** annotations agree | Same condition | **SOFT3-DO**: name is the slot. Mismatch with first-side `annotation is None` left `self.name` stuck and owner-won the second annotation. Always `AttributeError` on name mismatch. Dual-schema `Union[T, Validator]` that motivated valio’s “and annotations agree” is HOLD. |
| Annotation bind | L157–202: owner wins if self is `None`; `issubclassx` + owner overwrite if both set; write-back onto `owner.__annotations__` | Owner wins only if self is `None`; stdlib union identity; **no** write-back, **no** `_set_docs` | KEEP (Soft 2). Write-back / docs mutation DEFER. |
| Annotation conflict | `TypeError`, append, always re-raise (not debug-swallow) | Same | KEEP |
| `__set__` | default if `value is None`; store `pre_set` return; `post_set` after store | Same, Soft #2 falsy defaults | KEEP |
| `__get__` class | `return` (`None`) | `None` | KEEP (dataclass missing-default) |
| `__get__` instance | `pre_get(name)` then dict; `post_get` in `finally`; swallow → `None` | Same | KEEP |
| `__delete__` | `pre_delete` / `del` / `post_delete` in one `try` | Same | KEEP |
| debug-swallow | falsy swallows set/get/delete | Same; `__set_name__` does **not** swallow | KEEP |
| `ValidateProperty.pre_set` | L182–192 pipeline | L77–80 pipeline | KEEP — this **is** pre_set processing |
| Processor keys | L1757–1764, no `pre_set` | L593–604, no `pre_set` | KEEP — not a bug (see leftover teaching) |

**Pass 2 answer:** missing `pre_set` in the processors list is **intentional**.
`pre_set` **is** the validate pipeline (`add_pre_validator` /
`add_post_validator`). Inventing `add_pre_set` would dual-door the same phase.

---

## Pass 3 — Concern leaves + Soft #8 / #9 / #10 after Soft 2

| Lock | Still true? | Notes |
| --- | --- | --- |
| Soft #8 `None` ≠ `0` | Yes | `specified()` is None-only; `min_value=0` / `length=0` / `multiple_of=0` enforce. Tests in `tests/test_soft8_bound_honesty.py`. |
| Soft #8 inclusive/exclusive | Yes | `min`/`max` inclusive; `gt`/`lt` exclusive. |
| Soft #8 remainder | Yes | `multiple_of` uses `%`; `multiple_of=0` accepts only `0`. |
| Soft #9 compose-not-inherit | Yes | `Validator` bases `ValidateProperty` only. `tests/test_compose_not_inherit.py`. |
| Soft #10 processors then tasks once | Yes | No `asyncio.run` in `__set__`. `tests/test_processors_then_tasks.py`. |
| Soft #2 falsy defaults | Yes | `0` / `False` / `""` kept. |
| Soft 2 annotation conflict | Yes | Always-raise `TypeError`; not debug-swallow. |
| Reused validator | Partial | Same annotation + different name already `AttributeError`. **Hole:** first field unannotated, second annotated under a **different** name — name stayed, annotation owner-won. Soft3-DO. |
| Unions | Soft 2 identity KEEP; **runtime type check hole** | `int \| str` / `Optional[int]` identity at `__set_name__` is correct. `_is_instance_of` treated **every** `get_origin` like Union args: `list[int]` did `isinstance(value, (int,))` — rejected lists, accepted ints. `list[int] \| None` hit `TypeError` on parametrized `isinstance` and went **permissive** (accepted `1`). Soft3-DO. |
| Empty `ValidationPath` | Allowed | `ValidationPath(())` runs nothing. Not Door A caller surface (`ValidationPath` not in `__all__`). Residual. |
| debug-swallow vs `__set_name__` | Orthogonal | Set/get/delete swallow when `debug` falsy. Annotation `TypeError` at class body always raises (`debug=False` included). KEEP. |
| PEP 563 on **caller** | DEFER resolve | `from __future__ import annotations` makes owner annotation the string `'int'` vs facade `int` → `TypeError`. Labels both printed as `int`. Soft3-DO: quote string labels. Do **not** `eval` postponed annotations. |
| `in_choice=[]` | KEEP honesty | ux-valio enforces empty as empty (reject non-`None`). valio skipped via truthiness `and self.in_choice`. Soft #8 style: empty is specified. |
| Pattern `findall` empty-string groups | KEEP | valio `not any(findall)` treats `['']` as miss. ux-valio `if not findall` treats a non-empty list as a hit. `a?` on `"bbb"` is a real findall hit. Do not regress to `any()`. |

---

## Pass 4 — Failure domains

| Domain | What happens | Soft 3 |
| --- | --- | --- |
| Fail-open unknown kwargs | `Validator(expire_before=...)` landed in `Property.kwargs` and did **nothing**. Valio Door A named that kwarg (Soft #6 DEFER). Silent skip is a lie. | **SOFT3-DO**: drop `**kwargs` on `Property` / `Validator`. Python `TypeError: unexpected keyword argument`. |
| `Property(annotation=str)` | Stored in `kwargs`, `self.annotation` stayed `None`. | Same TypeError. Set `.annotation` after init or use a typed facade. |
| `post_set` after store | Value is already in `__dict__` if `post_set` raises. debug-True: caller sees failure, value remains. debug-falsy: swallowed, value remains. | KEEP — valio L264–274 same order. Rolling back would change Door A. Residual: document. |
| Swallowed set | Attribute unset; later get → `None`; `errors` append. | KEEP debug-swallow. |
| `pre_get` / `post_get` returns | Ignored. Get returns stored value (or `None` on swallow). | KEEP — only `pre_set` **hook** return stored. |
| Reassign counts | Increment in `post_set` after successful store. `id(obj)` keys. | KEEP. GC id reuse is a residual. |
| Shared validator state | Processors / counts live on the descriptor. Same name across classes is allowed; different names fail closed (after Soft3-DO). | KEEP intended share; namespace must match `instance.__class__.__name__`. Module-level `add_pre_validator` without `namespace=` does not fire. Residual footgun (valio same). |
| Mutable `default=[]` | Shared across instances (not callable). `default=list` is fine. | Residual / DEFER copy. valio same. |
| Parametrized generics | See Pass 3. Fail-open for `list[int]` (accepted `int`). | **SOFT3-DO** |
| `cache_task=True` | Accepted; does not cache. Tasks always run once per phase. | RETIRE cache behavior; KEEP kwarg so `cache_task=False` still means “don’t cache” (actual behavior). Not a silent missing feature like `expire_before`. |

---

## Pass 5 — Functionality parity table

Scope: valio Door A **CLAIMED ∩ EXPORTED ∩ LOCKED** for Soft 1 surface.
Fashion (MI, Field factory, Cap, typingx dual-schema) is out of scope.

| Surface | valio@3415c03 | ux-valio | Row |
| --- | --- | --- | --- |
| `field: T = SomeValidator(...)` | Yes | Yes | KEEP |
| `Validator` / `String` / `Integer` / `Boolean` facades | Yes (plus many named leaves) | Yes (A9×6 only) | KEEP |
| Descriptor 6 hooks | Yes | Yes | KEEP |
| Only `pre_set` **hook** return stored | Yes L264–268 | Yes | KEEP |
| `pre_validate` / `post_validate` processor bags | Yes | Yes | KEEP |
| `post_set` / get / delete processor bags | Yes | Yes | KEEP |
| `_processors["pre_set"]` / `add_pre_set` | **No** | **No** | KEEP — intentional; leftover-teach. Do not add. |
| Processors then tasks once | Soft #7 / #10 | Yes, sync | KEEP |
| Soft #2 falsy defaults | Yes | Yes | KEEP |
| Soft #8 bounds | Yes | Yes | KEEP |
| Soft #9 compose path | Soft #10 assemble | Yes | KEEP |
| Path fail-closed | Yes | Yes | KEEP |
| Pattern `findall` substring | Yes | Yes | KEEP |
| debug-swallow | Yes | Yes | KEEP — do not flip |
| Logger default OFF | ux-valio choice vs valio `logger=None` files | Yes | KEEP |
| Annotation conflict fail-closed | Yes | Soft 2 | KEEP |
| Stdlib union identity at bind | typingx `issubclassx` | `get_origin` / `get_args` | KEEP Soft 2 |
| Runtime `list[int]` / `dict[k,v]` / `tuple[...]` | `isinstancex` (HOLD dual-schema) | origin treated as Union args | **SOFT3-DO** — `isinstance` against origin; Union/Optional recurse; other origins TypeError → permissive (Soft 1) |
| Reused descriptor, different name | AttributeError only if annotations agree | Same hole | **SOFT3-DO** always name mismatch |
| Unknown / DEFER kwargs | Named `expire_*`, `has_attributes`, … | Silent `**kwargs` | **SOFT3-DO** TypeError |
| PEP 563 string label | n/a (valio forbids future annotations in validators) | Confusing `int` vs `int` | **SOFT3-DO** `repr` for `str` annotations |
| Soft #3 `PaymentCard` | Exported named leaf | Not on Soft 1 `__all__` | DEFER |
| Soft #4 named-once | `named_validate_once` | Not claimed | DEFER |
| Soft #6 `Expiry` / `expire_*` | On `Validator` + path unit | Not claimed | DEFER (now fail-closed if passed) |
| `has_attributes` / Attribute unit | On valio path | Not claimed | DEFER |
| `FloatValidator` / `Bytes` / `Email` / `Phone` / `Date` / `UUID` / `Enum` / containers | valio `__all__` | Not Soft 1 | DEFER named leaves |
| Dual-schema `Union[T, Validator]` + typingx | valio INT/STR aliases | HOLD | DEFER |
| `owner.__annotations__` write-back / `_set_docs` | Yes | No | DEFER |
| Door B `*Field` then `.validator` | README taught | Retired | RETIRE |
| Star-import 306 names | Yes | Explicit `__all__` | RETIRE |
| Concern-leaf MI diamond | Pre-Soft 10 | Compose | RETIRE |
| RGB/HSL crash leaves | Yes | No | RETIRE |
| `asyncio.run` in setter / TaskValidator loop | Yes | Sync tasks | RETIRE |
| Task result **cache** (`cache_task=True`) | asyncio task cache | No-op kwarg | RETIRE cache; KEEP param |
| Logger-on-by-`None` files | Yes | `None` → `False` | RETIRE |
| typing_extensions / typingx runtime dep | typingx | stdlib only | RETIRE as dep |
| Cap / Field twin / Schema twin / Result / `mount_channel` / `rule/` | Present in tree | Soft NOT | RETIRE / do not invent |

---

## Pass 6 — Diminishing returns (ship only Soft3-DO)

Ship in Soft 3 (existing Door A surface, honesty/bugs/holes):

1. **Parametrized generic type check** — `_is_instance_of` uses Union recursion;
   other origins `isinstance(value, origin)`; `TypeError` stays permissive.
   Element-wise `list[int]` content checks stay DEFER (typingx).
2. **Reused validator name** — `AttributeError` whenever `name != self.name`.
3. **Unknown kwargs fail-closed** — no `**kwargs` sink on `Property`/`Validator`.
4. **Annotation label** — string postponed annotations print as `repr` (`'int'`).
5. **Leftover-teach** — this doc + README + AGENTS: `pre_set` hook return vs
   processor bags. **No `add_pre_set`.**

Do **not** ship: Cap/Field/Schema, debug-swallow flip, typing_extensions,
PaymentCard/Expiry/named-once, `add_pre_set`, valio write-back, copying
mutable `default=[]`, rolling back store on `post_set` failure, PEP 563 eval.

### Residual risks still open

- PEP 563 on **caller** modules still fail-closed at class body (quoted label
  now honest). Resolving strings is DEFER.
- `post_set` failure leaves the stored value (valio parity).
- Processor `namespace` must match `__class__.__name__`.
- Shared mutable `default=[]`.
- `id(instance)` reassign map vs GC reuse.
- Parametrized generic **args** (list element types, `Literal`, `Annotated`)
  stay permissive / origin-only.
- `cache_task=True` does not cache.
- Empty `ValidationPath` is legal internally.
- Dataclass `slots` without `__dict__` is unclaimed.
- Soft #3 / #4 / #6 named leaves remain DEFER.
