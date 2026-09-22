# Performance

Stdlib Python is the apply path by default. The taught API does not
change for speed. An optional native peer is mapped in
[host / peer](host-peer-plan.md). ``ux-valio[native]`` may bind a
closed Integer or Float bound plan, a closed String or Bytes length plan,
or a closed IntegerEnum member-set plan,
or a closed StringEnum UTF-8 member-set plan,
or a closed Boolean exact-bool type door,
or a closed Decimal exact-Decimal type door,
at construct. Cap Door B
is not on this path.

## What is already compiled

At construct (`Validator.__init__` / `__set_name__`):

- specified default-path units (`_active_units`) — type always; length,
  value, pattern, choice, `reassign`, `multiple_of` only when you passed
  them
- named-facade extra (GSTIN checksum, Luhn, …) as one function after
  that path
- Pattern `re.compile` on the finder
- with `ux-valio[native]`, a closed Integer or Float bound plan (MinValue /
  MaxValue / GreaterThan / LessThan / Equal / range; type is FFI
  `i64` or `f64` extract, not an open type check) or a closed String or
  Bytes length plan (MinLength / MaxLength / Length / range; String type
  is FFI `&str` extract and count is `len(str)` codepoints; Bytes type
  is FFI `&[u8]` extract and count is `len(bytes)`) or a closed
  IntegerEnum member set (`Member` `i64` values; `compile_integer_enum`
  / `apply_integer_enum`) or a closed StringEnum UTF-8 member set
  (`compile_string_enum` / `apply_string_enum`) or a closed Boolean
  exact-bool type door (`compile_boolean` / `apply_boolean`; `1` / `0`
  are not coerced) or a closed Decimal exact-Decimal type door
  (`compile_decimal` / `apply_decimal`; `float` / `int` / `bool` are
  not coerced; no scale unit). Otherwise the interpreter
  still walks `_active_units`

At set, the interpreter walks that short tuple (or one FFI `apply_*` for
the closed native plan), then process hangs, then store on
`instance.__dict__`, then `post_set` / spawn `task_*`.

Mutating `min_value` after construct does nothing to the path. Pass
bounds at construct.

## What costs on the hot path

| work | when | note |
|---|---|---|
| specified units | every set | the loop you actually want |
| native `apply_*` | every set when the closed plan bound | one FFI; host still stores and raises |
| named extra | every set on that facade | checksums are cheap vs I/O |
| `pre_validate` / `post_validate` | every set | your code; keep it small |
| `post_set` | every successful set | persist/reserve; fail-closed |
| `task_*` | spawn, setter does not wait | I/O belongs here |
| `collect_all=True` | failures | continues remaining concerns; one failure still re-raises as itself |
| `logger=True` | every get/set/delete | info lines; leave OFF in tight loops |
| `debug=False` | failures | swallow + `errors` list; not faster on the success path |

`collect_all` is per-field, not per-dataclass. The first field that
fails still stops later fields. That is dataclass `__init__` order, not
a library bag.

## Versus Pydantic

Pydantic-core compiles a Rust plan and applies scalars natively.
ux-valio’s unconstrained `int` set is several Python calls (descriptor
`__set__`, specified units, store). Named identities (email, GSTIN) are
already competitive in Python — do not start a peer there.

A peer that calls back into Python **per unit** is slower than today.
One crossing per set, or none.

## Switch test (measured)

Bar: FAIL (KEEP Python) unless host ns/op ≥ **3×** native ns/op for
each closed Integer and Float bound family (`MinValue` / `MaxValue` /
`GreaterThan` / `LessThan` / `Equal` / min+max range) setattr vs
one-shot native `apply_integer(plan, i64)` / `apply_float(plan, f64)`, and each
closed String length family (`MinLength` / `MaxLength` / `Length` /
min+max range) vs `apply_string(plan, &str)`, and each closed Bytes
length family vs `apply_bytes(plan, &[u8])`, the closed IntegerEnum
member set vs `apply_integer_enum(plan, i64)`, the closed StringEnum
UTF-8 member set vs `apply_string_enum(plan, &str)`, and the closed
Boolean exact-bool type door vs `apply_boolean(plan, bool)`, and the
closed Decimal exact-Decimal type door vs `apply_decimal(plan, Decimal)`.

```console
python benches/measure_host_peer.py
```

Recorded 2026-09-21 on CPython 3.14.7 / rustc 1.83 / Linux x86_64:
host **3389–3515 ns/op**, native **46.2–46.5 ns/op**, ratio **73–76×**
for the first MinValue switch test. Bound-family re-run on a later
pod: host **2299–2415 ns/op**, native **93.6–99.4 ns/op**, ratio
**24.3–24.7×** for MinValue / MaxValue / GreaterThan / LessThan /
Equal / min+max range — all **PASS** the 3× bar. Float closed-plan
re-run on this tip: host **2441–2515 ns/op**, native **92.0–93.8 ns/op**,
ratio **26.3–26.9×** for the same six families — all **PASS**. String
length re-run on this tip: host **2399–2450 ns/op**, native **94.6–96.7
ns/op**, ratio **25.3–25.6×** for MinLength / MaxLength / Length /
min+max range — all **PASS**. Bytes length re-run on this tip: host
**2390–2434 ns/op**, native **93.2–95.7 ns/op**, ratio **25.3–25.9×**
for MinLength / MaxLength / Length / min+max range — all **PASS**.
IntegerEnum member-set re-run on this tip: host **3264 ns/op**, native
**94.6 ns/op**, ratio **34.5×** for ``Member(0..7)`` — **PASS**.
StringEnum UTF-8 member-set re-run on this tip: host **3421 ns/op**,
native **108.1 ns/op**, ratio **31.7×** for ``Member(m0..m7)`` —
**PASS**. Integer / Float / String / Bytes stayed ~24–25× and
IntegerEnum ~35× on that same run (still PASS).
Boolean exact-bool re-run on this tip: host **2991.4 ns/op**, native
**80.0 ns/op**, ratio **37.40×** — **PASS**. Integer / Float / String /
Bytes stayed ~27–29×, IntegerEnum ~38×, and StringEnum ~31× on that
same run (still PASS).
Decimal exact-Decimal re-run on this tip: host **6155.1 ns/op**, native
**79.8 ns/op**, ratio **77.09×** — **PASS**. Integer / Float / String /
Bytes stayed ~28–30×, IntegerEnum ~41×, StringEnum ~33×, and Boolean
~38× on that same run (still PASS). Host setattr includes
``DecimalValidator`` pre-validate and the named Decimal extra; native
is plan apply only.
Honesty: that ratio is descriptor
setattr vs **plan apply only** (product ``apply_integer`` uses
``Python::detach``). Do not claim the product extra is 70× end-to-end
after host store/raise. CI without Rust skips
(`python benches/measure_host_peer.py --ci`). Full notes, install, and
rejected shapes: [host / peer](host-peer-plan.md).

## What to do in application code

1. Put I/O in `post_validate` (lookup) and `post_set` (persist), not in
   `pre_validate`.
2. Background work is `task_post_set`, then `wait_tasks` at shutdown.
3. Do not wrap every field in `AllOf` of ten leaves if `StringValidator(min_length=3, pattern=…)`
   already specified the path.
4. Ports (`Validator[UserStore]`) run the type door once per construct —
   they are not the bottleneck.
5. `logger=True` is for diagnosis, not production hot paths.
6. `pip install ux-valio[native]` is optional. Call sites do not change.
