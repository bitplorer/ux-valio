# Soft 4 — valio intent pack (Door A hook / async honesty)

> **Soft 5 supersedes TypeError-at-register.** Soft 4 fail-closed `async def`
> at `add_*` because valio ran coroutines via `asyncio.run` in the setter.
> That was leftover honesty, not "async is illegal forever." Soft 5 restores
> registration and documents run rules. Soft 1 RETIRE of `asyncio.run` in
> `__set__` still holds. See `docs/soft5-async-callables.md`.
>

Frozen reference: [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4)
(Soft 10 compose). Soft-patch valio is **READ ONLY**.

ux-valio baseline: Soft 3 SHIP `635c9ae`. Public door stays
`field: T = SomeValidator(...)`. No Field / Schema / Cap / Result invented
here.

Council lock carried from Soft 3: **do not invent `_processors["pre_set"]` /
`add_pre_set`.** That bag is not in valio. Descriptor `pre_set` already owns
`pre_validate → validate → post_validate`. Soft 4 **does not reopen** it.

Soft 4 tip = the **named Soft4-DO honesty rows** in the table below
(cartograph vs `asyncio.run` RETIRE; sync/async `add_*` honesty;
decorator/`namespace` footguns; `enable_async` / `cache_task` claim vs tree)
plus this pack. Register DB-check is **Soft 3 KEEP** (`add_pre_validator`).

---

## Intent Lock refresh

Valio’s original product intent (README title + descriptor docstring, not the
Field factory) is **progressive validation that travels with dataclasses**:

1. A validator **is** the field default (`field: T = SomeValidator(...)`).
2. Assignment (`__set__`) is the validate moment. `None` takes `default`;
   falsy `0` / `False` / `""` stay (Soft #2 / E14).
3. Descriptor hooks are the lifecycle algebra. Only the **`pre_set` hook
   return** is stored. Everything after store is side-effect.
4. `ValidateProperty.pre_set` **is** the before-store pipeline
   (`pre_validation_processing` → `validate` → `post_validation_processing`).
   Hanging “before store” work uses **`add_pre_validator`** (transform,
   return kept) or **`add_validator`** (check, return ignored) or
   **`add_pre_validator_task`** (side-effect after processors, return
   ignored). There is no fifth door named `add_pre_set`.
5. Processors then tasks, once per phase (Soft #7 / #10). valio claimed
   generic sync/async by stuffing `asyncio.run` into that pipeline. That
   claim is **broken** (nested loops, `run_until_complete` without a running
   loop, `cache_task` keyed by `id(tasks)`). ux-valio **retires**
   `asyncio.run` in `__set__` and **fails closed** if an `add_*` callable is
   async or returns a coroutine. That is honesty, not a new public async door.
6. Dual-schema `Union[T, Validator]`, typingx, Field twin, Cap Host, Schema
   twin, `rule/`, Result, RGB/HSL, star-import barrel remain HOLD / RETIRE.

Door A usage that README implied but never named on the validator itself:

| Unstated README move | What it actually is | Door A today |
| --- | --- | --- |
| `@user_field.add_pre_valiator` (typo) | Field mixin delegates to `Validator.add_pre_validator` | Hang `@username_field.add_pre_validator` on the descriptor (`user_field` / `user` name split). `username: str = username` is `NameError`. |
| `@user_field.add_post_validator` `async def email_…` | Processor whose return is stored; valio would `asyncio.run` the coroutine | Sync callable only; async is TypeError |
| `@password_field.add_validator` | Extra check inside `validate()`; return ignored | `add_validator` |
| `valio.Validator.register(User)` | `ABC.register` virtual subclass, **not** a DB API | Do not teach. HOLD dual-schema |

---

## A. Full hook algebra (valio@3415c03)

Two layers. Do not collapse them.

### Layer 1 — `Property` descriptor hooks

`valio/descriptor/descriptors.py`:

| Hook | Defined | Called from | Return used by descriptor? |
| --- | --- | --- | --- |
| `pre_set` | L98–102 | `__set__` L264 | **Yes** — assigned into `obj.__dict__[self.name]` L265 |
| `post_set` | L104–108 | `__set__` L268 | **No** — call is statement, return dropped |
| `pre_get` | L110–114 | `__get__` L287 | **No** — `__get__` then returns `obj.__dict__[self.name]` L288 |
| `post_get` | L116–120 | `__get__` `finally` L300 | **No** |
| `pre_delete` | L122–126 | `__delete__` L316 | **No** |
| `post_delete` | L128–132 | `__delete__` L318 | **No** |

`__set__` order (L253–274): default if `value is None` → `pre_set` → **store**
→ `post_set`. Exception → append `errors`; re-raise only if `debug`.

`__get__` class access (`obj is None`, L278–279) returns `None` (implicit)
so dataclass treats the descriptor as a missing default.

`__get__` / `__delete__` pass **`self.name`**, not the stored value
(L287, L300, L316, L318).

### Layer 2 — `ValidateProperty` maps hooks → `*_processing`

`valio/validator/validators.py` L182–319:

```
pre_set  → pre_validation_processing → validate → post_validation_processing
post_set → post_set_processing
pre_get  → pre_get_processing
… same for post_get / pre_delete / post_delete
```

Base `*_processing` methods are identity (`return value`). They are
`@classmethod` on `ValidateProperty` (L210–319) and instance methods on
`Validator` (L1850–1952). ux-valio uses instance methods throughout.

### Layer 3 — `Validator` bags + `add_*`

**Processor bags** (L1757–1764). Seven. **No `pre_set`:**

- `_custom_pre_validator` ← `add_pre_validator` (L1860–1863)
- `_custom_post_validator` ← `add_post_validator` (L1875–1878)
- `_custom_post_set_processor` ← `add_post_set` (L1890–1893)
- `_custom_pre_get_processor` ← `add_pre_get` (L1905–1908)
- `_custom_post_get_processor` ← `add_post_get` (L1920–1923)
- `_custom_pre_delete_processor` ← `add_pre_delete` (L1935–1938)
- `_custom_post_delete_processor` ← `add_post_delete` (L1950–1953)

**Task bags** (`_init_task_state` L780–791). Same seven moments. **No
`pre_set` task bag.** Registration (`TaskValidator` L1516–1548, copied onto
`Validator` L1662–1668): `add_pre_validator_task`, `add_post_validator_task`,
`add_post_set_task`, `add_pre_get_task`, `add_post_get_task`,
`add_pre_delete_task`, `add_post_delete_task`.

**Custom validators** (not a processing bag): `_custom_validators` +
`add_validator` (L1828–1833). Run inside `_validate_field` **after** the
ordered path (L1802–1806). Return values are appended to a local list and
discarded by `validate()`.

Door B Field (`valio/field/fields.py` L124–182) is a **delegate** onto those
same methods. It does not add `add_pre_set` either.

### Return values: stored vs ignored

`_processing` (L1835–1848) **chains** `value = func(instance, value)` (or
`asyncio.run` of that). Whether that chained value is **stored** depends on
which hook `_processing` was called from:

| Caller | Chained processor return | Stored in `__dict__`? |
| --- | --- | --- |
| `pre_validation_processing` (inside `pre_set`) | becomes `pre_set` return | **Yes** |
| `post_validation_processing` (inside `pre_set`) | becomes `pre_set` return | **Yes** |
| `post_set_processing` | chained among processors | **No** (`__set__` ignores `post_set`) |
| get / delete processing | chained among processors | **No** |

Tasks: `_after_processing_run_tasks` (L807–811) always `return value`
unchanged. Task coroutine results are discarded. A **raising** task still
fails the surrounding hook (and therefore the set, unless debug-swallow).

### Namespace matching (unstated)

Every `add_*` keys the bag by
`namespace or str(func.__qualname__).split(".")[0]` (e.g. L1861–1862).
Run looks up `instance.__class__.__name__` (L1836, L1802).

- Method decorator inside `class Register:` → qualname `Register.fn` →
  namespace `Register` → **fires**.
- Module-level function without `namespace=` → namespace is the **function
  name** → **silent no-op**. valio same. Soft 4 leftover-teaches; does not
  invent a mismatch exception (cannot distinguish “no processors” from
  “wrong namespace”).

---

## Hook moment table

| Moment | Bag / API | Return stored? | sync / async? | valio@3415c03 | ux-valio |
| --- | --- | --- | --- | --- | --- |
| `__set__` default | — | `None` only → `default` | sync | `descriptors.py` L262–263 | `descriptor.py` L155–159 |
| `pre_set` **hook** | not a bag | **Yes** | sync; *is* the pipeline | `descriptors.py` L264–265; `validators.py` L182–192 | `descriptor.py` L159–161; `validators.py` L115–118 |
| pre-validate processors | `_custom_pre_validator` / `add_pre_validator` | **Yes** (inside hook) | valio: sync, or `asyncio.run` if coroutine / `enable_async`; ux: **sync only** | `validators.py` L1850–1863, `_processing` L1835–1848 | `validators.py` L716–719, L680–683, L695–696 |
| pre-validate tasks | `_pre_validate_tasks` / `add_pre_validator_task` | **No** | valio: wrap + `asyncio.run(_job)`; ux: sync call, return ignored | L807–811, L1516–1553, L1856–1858 | `validators.py` L751–754, L685–688 |
| `validate()` path units | `_validation_path` | n/a (raise or pass) | valio sync path unless `enable_async` | L1780–1807, L1631–1642 | `validators.py` L668–669 |
| extra checks | `_custom_validators` / `add_validator` | **No** | valio: `run_until_complete` if `iscoroutinefunction`; ux: **sync only** | L1802–1806, L1828–1833 | `validators.py` L672–678 |
| post-validate processors | `_custom_post_validator` / `add_post_validator` | **Yes** | same as pre-validate | L1865–1878 | `validators.py` L721–724, L698–699 |
| post-validate tasks | `_post_validate_tasks` | **No** | same as pre-validate tasks | L1521–1524, L1871–1873 | `validators.py` L756–759 |
| **store** | `obj.__dict__[name] = value` | — | sync | `descriptors.py` L265 | `descriptor.py` L160 |
| `post_set` hook | not a bag | **No** | sync | `descriptors.py` L268; `validators.py` L221–232 | `descriptor.py` L161; `validators.py` L120–121 |
| post-set processors | `_custom_post_set_processor` / `add_post_set` | **No** | valio async-capable; ux sync | L1880–1893 | `validators.py` L726–729, L701–702 |
| post-set tasks | `_post_set_tasks` | **No** | valio `asyncio.run`; ux sync | L1526–1528, L1886–1888 | `validators.py` L761–764 |
| `pre_get` / `post_get` | `add_pre_get` / `add_post_get` (+ `_task`) | **No**; see **name** not value | valio async-capable; ux sync | `descriptors.py` L287–300; `validators.py` L1895–1923 | `descriptor.py` `__get__`; `validators.py` L731–739 |
| `pre_delete` / `post_delete` | `add_pre_delete` / `add_post_delete` (+ `_task`) | **No**; see **name** | same | `descriptors.py` L316–318; `validators.py` L1925–1953 | `descriptor.py` `__delete__`; `validators.py` L741–749 |
| `_processors["pre_set"]` / `add_pre_set` | **does not exist** | — | — | bags L1757–1764; Field L124–182 | `validators.py` L630–641; `tests/test_soft3_honesty.py` |

---

## B. Register DB-check — which Door A API?

User ask: *decorator checking users in DB before setting username on a
Register class. Can't there be pre_set processing or tasks?*

**Yes, there is before-store processing and before-store tasks.** They are
not named `pre_set`.

valio README (`README.md` L63–129) teaches a **RegisterUser** example:

```79:85:README.md
    @user_field.add_pre_valiator
    def user_not_in_db(self, user: User):
        # logic goes here....
        
    @user_field.add_post_validator
    async def email_user_activity(self, user: User):
```

Facts:

1. **Typo:** `add_pre_valiator` is not an attribute. Field defines
   `add_pre_validator` (`valio/field/fields.py` L128–130), which calls
   `self.validator.add_pre_validator(func)` (`validators.py` L1860–1863).
2. That decorator is Door B (`UserField` / `StringField`) wrapping Door A.
   ux-valio retired Door B. The Door A hang is on the descriptor itself.
3. `user_not_in_db` is a **processor** (`add_pre_validator`), not a task.
   It runs inside `pre_set` **before** `validate` and **before** store.
   Its return **is stored**. An implicit `None` would store `None`.
4. A raise-only uniqueness check also fits **`add_validator`**
   (`validators.py` L1828–1833), which runs inside `validate()` after path
   units; return ignored. Still before store.
5. **`add_pre_validator_task`** also runs before store (after processors,
   L1856–1858). Return ignored. valio default `cache_task=True` keys cache
   by `id(tasks)` (the bag dict, L1494–1500) — a uniqueness task would
   **not re-check** later assignments. Wrong tool for “is this username
   taken?”.
6. **`add_pre_set` does not exist** in valio bags, Field mixin, or
   TaskValidator. Inventing it would dual-door the same moment as
   `add_pre_validator` (E14). Soft 3 KEEP stands. Soft 4 does **not** reopen.

**Door A answer (Soft 4 leftover teaching):**

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
        return value  # processor return is stored
```

Raise-only variant: `@username_field.add_validator` (do not need to return
`value`). Side-effect-only variant: `@username_field.add_pre_validator_task`
(does not rewrite the stored username; a raise still blocks the set).

`username: str = username` is `NameError` — the class-body assignment makes
`username` local, so the RHS cannot see the outer descriptor. valio README
avoided this with Door B’s `user_field` / `user` split (L65–127).

`valio.Validator.register(User)` in the same README (L51) is
`abc.ABC.register` — virtual subclassing for dual-schema
`Union[User, Validator]`. It is **not** the Register DB API. HOLD.

---

## C. Async: CLAIMED vs LOCKED vs broken

| Surface | valio@3415c03 CLAIMED | LOCKED / BROKEN | ux-valio Soft 4 |
| --- | --- | --- | --- |
| `asyncio.run` in setter pipeline | `_after_processing_run_tasks` L809; `_processing` L1842 / L1846; `_async_validate_field` L1826 | Nested `asyncio.run` from `__set__` fails if a loop is already running. Soft NOT | **RETIRE** — never `asyncio.run` in `__set__` |
| `enable_async` | ctor L1698, flag L1756, `validate()` L1782–1785 | Default `None` is falsy → sync path. Commented `__main__` L2463 shows the claim. No tests | **not a kwarg** (Soft 3 unknown-kwargs TypeError). Do not invent |
| Processor sync/async | `_processing` L1837–1846: if `enable_async`, wrap every func; else if `iscoroutine(value)`, still `asyncio.run` | Hidden async door even when `enable_async` is off | **Soft4-DO:** async callable TypeError at `add_*`; coroutine **result** TypeError at run (not stored) |
| Task sync/async | `add_*_task` wraps sync via `async_wrap` (L1518, L1956–1963) then `_job` | `_job` `while self.ok` (L1491) still **returns** after one batch; `task_interval` is delay-before-first, not a daemon. `cache_task=True` caches by `id(tasks)` | Sync call, once per phase. `cache_task` kwarg KEEP, cache behavior RETIRE |
| `add_validator` async | `run_until_complete` (L1803–1804) | Needs a **running** loop; `__set__` usually has none → `RuntimeError` | TypeError at `add_validator` if coroutinefunction |
| README `async def email_user_activity` on `add_post_validator` | Would hit `_processing` coroutine branch | Relies on `asyncio.run` in `__set__` | TypeError at decorate time |
| `async_wrap` + executor | L1956–1963 | Thread offload of sync work under a forbidden `asyncio.run` | Do not port |
| debug-swallow + async | Failures append `errors`; `debug` falsy swallows | A swallowed coroutine TypeError would leave the attribute unset (same as any other set error) | KEEP swallow. Registration-time TypeError is **outside** `__set__` so it always raises |
| Cap / Host / mount_channel | not required for Door A async | HOLD invent | **STOP** if a Soft4-DO would need them |

**What Soft 4 may KEEP / DEFER / DO without inventing Cap**

- **KEEP:** no `asyncio.run` in `__set__`; no `enable_async` door; no Cap.
- **DO:** fail-closed honesty on existing `add_*` / `add_*_task` /
  `add_validator` (this pack + tests + TypeError).
- **DEFER:** real async Door A (running caller’s loop, scheduling tasks
  after `__set__`, Cap Host). That is a new product, not a tip.

---

## D. Tasks vs processors

| | Processors (`add_pre_validator`, `add_post_set`, …) | Tasks (`add_*_task`) |
| --- | --- | --- |
| When | First in the phase (`_processing` / `_run_processors`) | After processors, same phase (`_after_processing_run_tasks` / `_run_tasks`) |
| Return | Chained as `value` | Ignored |
| valio async | optional `asyncio.run` per func | always wrapped; `asyncio.run(_job)` |
| `cache_task` | n/a | valio: skip re-run when `task[id(tasks)]` filled; ux: **no cache** |
| DB uniqueness | **Yes** if raise + (for processors) return the value | Only if raise; valio cache makes it a one-shot lie |
| README encrypt password | `add_post_validator` **must** return the hash (stored) | Wrong layer |

ux-valio vs valio honesty gaps Soft 4 closes:

1. Hanging `async def` on `add_pre_validator` **stored a coroutine object**.
   valio would have `asyncio.run`’d it. Storing the coroutine is a lie.
2. Hanging `async def` on a task created a never-awaited coroutine
   (`RuntimeWarning`) instead of running or refusing.
3. `enable_async` was claimed on valio and is **absent** on ux-valio;
   `cache_task=True` is claimed-as-cache on valio and is a no-op kwarg here.
4. Module-level `add_*` without `namespace=` is a silent no-op; class-body
   `username: str = username` is `NameError`.

---

## E. Unstated usage (observe, do not invent)

| Concern | valio@3415c03 | ux-valio | Soft 4 |
| --- | --- | --- | --- |
| Reused validator, same name, two classes | Allowed; bags keyed by class name | Soft 3: same name OK; different name `AttributeError` | KEEP |
| Namespace miss (module-level decorator, no `namespace=`) | Silent no-op (L1861 vs L1836) | Same | Soft4-DO leftover-teach + test. Do not invent fail-closed mismatch |
| Class-body `username: str = username` | README used Door B `user_field` / `user` (L65–127) | `NameError` (name is local) | Soft4-DO cartograph. Hang `username_field` |
| Nested class / test-local class | `test_fn.<locals>.Host.fn` → first segment `test_fn` | Same silent no-op | Soft4-DO: pass `namespace="Host"` or define the class at module level |
| Logger default | `logger=None` → file logs (`loggers.py` L58–78) | `None` coerced to `False` (OFF) | KEEP Soft 1 |
| debug-swallow | falsy swallows set/get/delete; `__set_name__` always raises | Same | KEEP — do not flip |
| debug-swallow + async TypeError at **run** | would swallow | swallows | KEEP. Prefer TypeError at **`add_*`** so `async def` never reaches `__set__` |
| Shared `default=[]` | descriptor default is the object | Same | DEFER copy. Document |
| Dataclass field default **is** the validator | README User / Accounts | Door A KEEP | KEEP |
| `post_set` failure after store | value remains | Same | KEEP (valio parity). Residual |
| `Validator.register(User)` | ABC virtual subclass | `ValidateProperty` is still ABC so `.register` exists | Do not teach. HOLD dual-schema |
| PEP 563 on caller | forbidden inside validators.py (L8–10) | Soft 3 quotes string labels | DEFER resolve |
| Mutable processor lists on a shared descriptor | intended share | Same | KEEP |
| `in_choice=[]` truthiness | valio skipped empty | ux enforces empty | KEEP Soft #8 style |

---

## Soft4 KEEP

| Lock | Cite / test |
| --- | --- |
| Door A `field: T = SomeValidator(...)` | README; `tests/test_door_a_readme.py` |
| No `_processors["pre_set"]` / `add_pre_set` / `add_pre_set_task` | valio bags L1757–1764; `tests/test_soft3_honesty.py`; `test_no_add_pre_set_still_absent` |
| `pre_set` hook **is** pre_validate → validate → post_validate | valio L182–192 |
| Register DB-check = `add_pre_validator` inside `pre_set` | valio L1860–1863; README L79–81 typo; Soft 3 KEEP |
| Soft #2 falsy defaults | `tests/test_soft2_falsy_defaults.py` |
| Soft #8 `None` ≠ `0` | `tests/test_soft8_bound_honesty.py` |
| Soft #9 compose-not-inherit | `tests/test_compose_not_inherit.py` |
| Soft #10 processors then tasks once | `tests/test_processors_then_tasks.py` |
| Path fail-closed | `tests/test_path_fail_closed.py` |
| Pattern `findall` | `tests/test_pattern_findall.py` |
| debug-swallow | `tests/test_door_a_readme.py` — **do not flip** |
| Logger default OFF | `test_logger_defaults_off` |
| Annotation conflict fail-closed | `tests/test_annotation_conflict.py` |
| Soft 3 generics / reuse / unknown kwargs | `tests/test_soft3_honesty.py` |
| No `asyncio.run` in `__set__` | Soft 1 RETIRE; valio L807–811 / L1835–1846 is the retired claim |
| No Cap / Field / Schema / Result / `mount_channel` / `rule/` | `__all__` |
| Soft #3 PaymentCard / #4 named-once / #6 Expiry | still DEFER |

## Soft4-DO (this PR — named honesty rows only)

| Row | Why it is a tip, not a new door | valio@3415c03 cite | ux-valio |
| --- | --- | --- | --- |
| **Cartograph Door A unstated usage vs Soft 1 RETIRE of `asyncio.run` in `__set__`** | README hung `async def email_user_activity` on `add_post_validator` (L83–85) expecting the setter to drive async. Soft 1 retired `asyncio.run` in `__set__`. Storing a coroutine object would be a lie. Class-body `username: str = username` is `NameError`; Door B used `user_field` / `user` (L65–127). | `_after_processing_run_tasks` L807–811 (`asyncio.run(main(obj._job(...)))`); `_processing` L1844–1846 (`if asyncio.iscoroutine(value): value = asyncio.run(...)`); `Property.__set__` L264–268 (sync store of `pre_set` return); README L83–85, L65–127 | Soft 4 leftover: `inspect.iscoroutine` TypeError'd (did not run). **Soft 5:** coroutine objects follow run rules (drive if loop; Soft 5 Door if not). Hang `username_field`. Tests: `test_no_asyncio_run_or_enable_async_in_door_a_tree`, `test_same_name_descriptor_and_field_is_nameerror`; Soft 5 `test_sync_processor_returning_coroutine_*` |
| **sync vs async processor/task registration honesty** | valio wrapped sync tasks (`async_wrap` L1956–1963) and optionally processors (`enable_async` L1837–1842). ux-valio has **0** `enable_async` as a door. Soft 4 TypeError'd `async def` at `add_*` and coroutine **results** at run. | `enable_async` ctor L1698, flag L1756, `validate()` L1782–1785, `_processing` L1837–1846; `add_pre_validator_task` L1516–1518 (`iscoroutinefunction` else `async_wrap`); `_after_processing_run_tasks` L807–811 | Soft 4 leftover `_require_sync_callable` / `_reject_coroutine_result`. **Soft 5:** both gone; register OK; run rules. Tests: `test_async_def_add_*_registers`, `docs/soft5-async-callables.md` |
| **decorator / `namespace` footguns** | Bags key by `namespace or qualname.split(".")[0]`; run looks up `instance.__class__.__name__`. Module-level decorator without `namespace=` is a silent no-op. Method decorator matches only on a **module-level** class. Nested/`<locals>` classes need `namespace=`. Processor `None` return **is** stored. | `add_pre_validator` L1860–1863; `_processing` L1836; `add_validator` L1831–1832 | `_namespace` docstring. Tests: `test_module_level_decorator_without_namespace_does_not_fire`, `test_module_level_decorator_with_namespace_fires`, `test_method_decorator_namespace_matches_module_level_class`, `test_nested_class_method_decorator_qualname_does_not_match`, `test_add_pre_validator_implicit_none_is_stored` |
| **claim vs tree for `enable_async` / `cache_task`** | valio claimed `enable_async` and `cache_task=True` (cache by `id(tasks)`). ux-valio Soft 1 tree: **0** `enable_async`; `cache_task` kwarg exists but **does not cache**. Do not invent the missing door; do not silently pretend cache works. | `enable_async` L1626, L1698, L1756, L1782–1785, L1837; `cache_task` `_init_task_state` L780–789; `_job` L1495–1500 | `enable_async=True` → `TypeError` (Soft 3 unknown kwargs). `cache_task=True` still runs every assignment. Tests: `test_enable_async_kwarg_is_type_error_not_a_new_door`, `test_cache_task_true_does_not_cache_tasks` |

## Soft4 DEFER

| Row | Why not this tip |
| --- | --- |
| Invent `add_pre_set` / `_processors["pre_set"]` | No valio bag. E14 dual-door. **Soft 3 KEEP closed — do not flip** |
| Restore `enable_async` / `async_wrap` / `asyncio.run` in `__set__` / Cap Host | New async product. STOP |
| Soft #3 PaymentCard / #4 named-once / #6 Expiry | Named leaves, not hook honesty |
| Field / Schema twins, dual-schema, typingx, pyparsing | HOLD |
| Copy mutable `default=[]` | valio same share |
| Fail-closed namespace mismatch | Cannot distinguish empty bag from wrong name without a new signal |
| PEP 563 eval on caller | Soft 3 quotes; resolve DEFER |
| Rollback store on `post_set` failure | Changes Door A |
| Element-wise `list[int]` | typingx HOLD |
| `task_interval` repeating job | valio `_job` does not actually loop-run |
| Make `cache_task=True` actually cache | RETIRE cache; KEEP kwarg (claim vs tree is the tip) |

## Soft4 RETIRE

| Row | Notes |
| --- | --- |
| Door B `*Field` then `.validator` | Soft 1; README RegisterUser uses it — Door A `username_field` hang replaces it |
| `asyncio.run` / `run_until_complete` inside `__set__` | Soft 1 RETIRE; Soft 4 does not restore |
| Task result cache | valio L1495–1500; ux no-op kwarg |
| Logger-on-by-`None` files | Soft 1 |
| Star-import barrel, MI diamond, RGB/HSL | Soft 1 |
| Teaching `Validator.register` as a DB/schema API | It is `ABC.register` |

---

## Explicit answer (user DB-check) — Soft 3 KEEP

**Register username uniqueness before store uses `add_pre_validator`
(processor, return the value).** It runs inside descriptor `pre_set`,
before `__dict__` store.

Cite: valio `ValidateProperty.pre_set` L182–192 + `add_pre_validator`
L1860–1863. README L79 `@user_field.add_pre_valiator` is a typo for Field
`add_pre_validator` (`valio/field/fields.py` L128–130).

It does **not** use `add_pre_set` (no such API — bags L1757–1764). Soft 3
absence lock stands. Soft 4 does **not** reopen it.

Hang the descriptor as `username_field` (Door B name split). Soft 4’s named
rows above are the honesty tip around that KEEP (async refuse, namespace,
`enable_async` / `cache_task` claim vs tree).
