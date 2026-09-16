# AGENTS.md

Door A only: `field: T = SomeValidator(...)`.

- Frozen reference: `bitplorer/valio` @ `3415c03`. Do not edit valio.
- No Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`,
  Result type, RGB/HSL, or star-import barrel.
- No `asyncio.run` in `__set__`. Nested loops use the nest-safe worker
  bridge only.
- No `add_pre_set` / `_processors["pre_set"]` (that would be a second door).
- KEEP: falsy assigned `0` / `False` / `""` are not replaced by `default`;
  `default=[]` is shared; `default_factory=` is per-instance; both set is
  TypeError; callable `default=` still invoked (valio leftover);
  bound honesty (`None` ≠ `0`); debug-swallow; logger default OFF;
  never-set `__get__` / `__delete__` with `debug=True` is named
  `AttributeError`, not bare `KeyError`;
  Pattern `findall`; facades do not multiple-inherit concern leaves;
  path fail-closed; processors then tasks once;
  `pre_set` hook IS the validate pipeline (no processor bag named `pre_set`);
  before-store hangs on `add_pre_validator` / `add_validator` /
  `add_pre_validator_task`; `add_*` accepts async def and coroutine
  results (no `_reject_coroutine_result`);
  sync path with no running loop TypeError names the missing loop / helper;
  running loop uses nest-safe worker bridge.
  `enable_async` is not a door (unknown-kwarg TypeError).
  `cache_task` kwarg KEEP, cache behavior RETIRE. Accepted on `Validator`
  and on compose roots (`AllOf` / `AnyOf`); it does not skip re-checks.
  `collect_all` default False (fail-fast). Do not overload `debug` into
  collect-all. Hang `add_*` on `Validator` or the compose root (`AllOf` /
  `AnyOf`), not concern leaves. Compose merge fail-closed: conflicting
  specified `debug` / `default` / `default_factory` / `collect_all` /
  `logger` is TypeError.
  Explicit `False` is specified. Omitted `collect_all` / `logger` still
  collapse to a specified `True`. `Chain` is `AllOf`.
  Unresolved owner `str` / `ForwardRef` annotations TypeError at bind
  (not copied, not eval'd). `AnyOf` does not AND-gate root type; `AllOf`
  keeps annotation-conflict TypeError. Unknown path unit is `ValueError`.
  TypedDict membership stays fail-closed on the private helper. Callable
  origin is checked; signature is not. Generic subclass instance params
  are not inspected.
- Validator objects compose with `&` / `|` or `AllOf` / `AnyOf`.
  That is object composition, not leaf multiple-inheritance.
- `AttributeValidator` is not shipped. Object-attribute presence checks
  belong at the call site or on `add_validator`.
- `PaymentCardValidator` is brand ∩ Luhn (stdlib `re`; a Luhn-valid
  generator is not enough). `AadhaarCardValidator` is 12-digit identity ∩
  Verhoeff. `PANCardValidator` is identity `fullmatch` ∩ Luhn mod 26
  (complete A–Z; a format-only generator is not enough). `ExpiryValidator`
  is a Door A facade with exclusive `expire_after` / `expire_on` /
  `expire_before`. `expire_before` is its own bound. `expire_*` are not
  kwargs on `Validator`. No `expiry` path unit.
- Named typed facades call their extra check from `validate()` after the
  inherited path; they do not `add_validator` themselves on each assignment.
  `collect_all=True` continues into that extra check. No NamedOnce Cap.
  `HexColorValidator` is not a public facade. `DateValidator` rejects
  `datetime.datetime`. Pattern `&` / `|` is fail-closed on missing or mixed
  `str`/`bytes` fragments; inverted `count_min` / `count_max` is
  constructor `ValueError`; bytes patterns keep bytes identity.
