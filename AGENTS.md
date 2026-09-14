# AGENTS.md

**Soft LOCK.** Soft DO = Soft 5 restore async add_*/tasks (no asyncio.run in `__set__`).

- Frozen reference: `bitplorer/valio` @ `3415c03`. Do not edit valio.
- Public door: `field: T = SomeValidator(...)`.
- Soft NOT: Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`,
  Result type, RGB/HSL, star-import barrel, `asyncio.run` in `__set__`,
  `add_pre_set` / `_processors["pre_set"]` (E14 dual-door).
- KEEP: Soft #2 falsy defaults; Soft #8 bound honesty (`None` ≠ `0`);
  debug-swallow; logger default OFF; Pattern `findall`; compose-not-inherit;
  path fail-closed; processors then tasks once;
  `pre_set` hook IS the validate pipeline (no processor bag named `pre_set`);
  before-store hangs on `add_pre_validator` / `add_validator` /
  `add_pre_validator_task`; `add_*` accepts async (Soft 5 register OK);
  sync path with no running loop TypeError names Soft 5 Door; running loop
  uses nest-safe worker bridge (never `asyncio.run` in `__set__`).
  `enable_async` is not a door (unknown-kwarg TypeError).
  `cache_task` kwarg KEEP, cache behavior RETIRE.
