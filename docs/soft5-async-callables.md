# Soft 5 — restore async add_*/tasks (no asyncio.run in `__set__`)

Frozen reference: [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4).
Soft-patch valio is **READ ONLY**. Baseline: Soft 4 SHIP `63f1cfe`.

Public door stays `field: T = SomeValidator(...)`. No Field / Schema / Cap /
`add_pre_set`. Soft #3 / #4 / #6 named leaves still DEFER.

---

## Leftover teaching: Soft 4 rejected TWO things (both temporary)

User ask: *Why `require_sync_callable` on tasks? Can't decorate async
functions?* Follow-up: *Also why rejecting async coroutines?*

Soft 4 fail-closed **both** because valio drove them with `asyncio.run` in
the setter. Neither reject is permanent degradation.

| Soft 4 reject | What it caught | valio@3415c03 drive (RETIRED) | Soft 5 |
| --- | --- | --- | --- |
| `_require_sync_callable` at `add_*` | `async def` / coroutine **functions** | `add_*_task` kept coroutinefunctions (L1516–1518); `enable_async` + `async_wrap` (L1956–1963); README `async def email_user_activity` | **Register OK.** Hang `@field.add_pre_validator` / `add_post_*` / `add_*_task` on `async def`. |
| `_reject_coroutine_result` at run | coroutine **objects** (sync wrap that `return coro(...)`, or calling the async def) | `_processing` L1844–1846 `if asyncio.iscoroutine(value): value = asyncio.run(...)` | **Not a class reject.** Drive via nest-safe bridge if a loop is running; Soft 5 Door TypeError if not. Never store the coroutine. Never `asyncio.run` in `__set__`. |

valio accepted `async def` on `add_pre_validator` / `add_post_*` / `add_*_task`
and drove the coroutine from the setter pipeline:

| valio@3415c03 | What it did |
| --- | --- |
| `_processing` L1835–1846 | If `enable_async`, wrap via `async_wrap` then `asyncio.run`. Else if `iscoroutine(value)`, still `asyncio.run`. |
| `_after_processing_run_tasks` L807–811 | `asyncio.run(main(obj._job(...)))` after processors. |
| `add_*_task` L1516–1518 | Keep coroutinefunctions; wrap sync with `async_wrap` (L1956–1963, `run_in_executor`). |
| `add_validator` L1803–1804 | `run_until_complete` if `iscoroutinefunction`. |
| README L83–85 | `@user_field.add_post_validator` / `async def email_user_activity`. |

That `asyncio.run` in the setter is a **nested-loop hazard**. Soft 1 RETIRED
it. Soft 4 then refused `async def` at `add_*` **and** TypeError'd coroutine
objects at run so ux-valio would not store a coroutine or leak a
never-awaited task. That fail-closed was **honesty**, not a product claim
that async / coroutines are illegal forever.

Soft 5 restores valio's registration (coroutine **functions** may hang on
`add_*`) and treats coroutine **objects** as work to drive under run rules
that do **not** bring `asyncio.run` / `run_until_complete` back inside
`Property.__set__`.

---

## Soft5-DO (locked approach)

**Register OK.** `add_pre_validator` / `add_post_*` / `add_validator` /
`add_*_task` accept async defs **and** sync callables that will return a
coroutine. No `_require_sync_callable`. No `_reject_coroutine_result`.

**Run rules** when an async callable (or a sync callable that returns a
coroutine) is invoked on the **sync descriptor path**:

1. **No running loop** (`asyncio.get_running_loop()` raises `RuntimeError`)
   → `TypeError` naming **Soft 5 Door**:
   `await from async context / call via Soft5 helper`.
   Close the coroutine. Do not store it. Do not `asyncio.run`.
2. **Running loop exists** → nest-safe sync-bridge: drive the coroutine on a
   **private loop in a worker thread**. Same-thread `run_until_complete` on
   the caller's loop *is* the nested-loop hazard Soft 1 retired; waiting
   `run_coroutine_threadsafe(...).result()` on the loop thread deadlocks.
   The worker never touches the caller's loop.

Assign from an async context (`asyncio.run` of a small harness, or
pytest-asyncio) so rule 2 applies. Sync `Host(x=...)` with no loop hits
rule 1.

`enable_async` stays **not a door**. `cache_task` kwarg KEEP, cache RETIRE.
debug-swallow KEEP: a Soft 5 Door `TypeError` at run is swallowed when
`debug` is falsy (attribute unset), and re-raised when `debug=True`.

---

## Soft5 KEEP

| Lock | Cite / test |
| --- | --- |
| No `asyncio.run` / `run_until_complete` in `__set__` | Soft 1 RETIRE; `test_no_asyncio_run_in_set` |
| No `_require_sync_callable` / `_reject_coroutine_result` | Soft 5; `test_no_add_pre_set_still_absent` |
| No `add_pre_set` | Soft 3; `test_no_add_pre_set_still_absent` |
| debug-swallow | `test_sync_processor_returning_coroutine_debug_falsy_swallows_unset` |
| Soft #2 / #8 / annotation / compose / path / findall | existing tests |
| `enable_async` unknown-kwarg TypeError | `test_enable_async_kwarg_is_type_error_not_a_new_door` |
