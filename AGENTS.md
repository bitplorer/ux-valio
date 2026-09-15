# AGENTS.md

Door A only: `field: T = SomeValidator(...)`.

- Frozen reference: `bitplorer/valio` @ `3415c03`. Do not edit valio.
- No Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`,
  Result type, RGB/HSL, or star-import barrel.
- No `asyncio.run` in `__set__`. Nested loops use the nest-safe worker
  bridge only.
- No `add_pre_set` / `_processors["pre_set"]` (that would be a second door).
- KEEP: falsy assigned `0` / `False` / `""` are not replaced by `default`;
  bound honesty (`None` ≠ `0`); debug-swallow; logger default OFF;
  Pattern `findall`; facades do not multiple-inherit concern leaves;
  path fail-closed; processors then tasks once;
  `pre_set` hook IS the validate pipeline (no processor bag named `pre_set`);
  before-store hangs on `add_pre_validator` / `add_validator` /
  `add_pre_validator_task`; `add_*` accepts async def and coroutine
  results (no `_reject_coroutine_result`);
  sync path with no running loop TypeError names the missing loop / helper;
  running loop uses nest-safe worker bridge.
  `enable_async` is not a door (unknown-kwarg TypeError).
  `cache_task` kwarg KEEP, cache behavior RETIRE.
  `collect_all` default False (fail-fast). Do not overload `debug` into
  collect-all. Hang `add_*` on `Validator` or the compose root (`AllOf` /
  `AnyOf`), not concern leaves. Compose merge fail-closed: conflicting
  specified `debug` / `default` is TypeError. `Chain` is `AllOf`.
- Validator objects compose with `&` / `|` or `AllOf` / `AnyOf`.
  That is object composition, not leaf multiple-inheritance.
- `AttributeValidator` is not shipped. Object-attribute presence checks
  belong at the call site or on `add_validator`.
- Payment-card / named-once / expiry leaves stay out of this tree.
