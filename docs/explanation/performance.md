# Performance

Stdlib Python is the apply path by default. The taught API does not
change for speed. An optional native peer is mapped in
[host / peer](host-peer-plan.md). ``ux-valio[native]`` may bind a
closed Integer bound plan at construct. Cap Door B
is not on this path.

## What is already compiled

At construct (`Validator.__init__` / `__set_name__`):

- specified default-path units (`_active_units`) — type always; length,
  value, pattern, choice, `reassign`, `multiple_of` only when you passed
  them
- named-facade extra (GSTIN checksum, Luhn, …) as one function after
  that path
- Pattern `re.compile` on the finder
- with `ux-valio[native]`, a closed Integer bound plan (MinValue /
  MaxValue / Gt / Lt / Eq / range; one owned Rust `Plan`) — otherwise
  the interpreter still walks `_active_units`

At set, the interpreter walks that short tuple (or one FFI `apply` for
the closed native plan), then process hangs, then store on
`instance.__dict__`, then `post_set` / spawn `task_*`.

Mutating `min_value` after construct does nothing to the path. Pass
bounds at construct.

## What costs on the hot path

| work | when | note |
|---|---|---|
| specified units | every set | the loop you actually want |
| native `apply` | every set when the closed plan bound | one FFI; host still stores and raises |
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
each closed Integer bound family (`MinValue` / `MaxValue` / `Gt` /
`Lt` / `Eq` / min+max range) setattr vs one-shot native
`apply(plan, i64)`.

```console
python benches/measure_host_peer.py
```

Recorded 2026-09-21 on CPython 3.14.7 / rustc 1.83 / Linux x86_64:
host **3389–3515 ns/op**, native **46.2–46.5 ns/op**, ratio **73–76×**
for the first MinValue switch test. Bound-family re-run on a later
pod: host **2299–2415 ns/op**, native **93.6–99.4 ns/op**, ratio
**24.3–24.7×** for MinValue / MaxValue / Gt / Lt / Eq / min+max
range — all **PASS** the 3× bar. Honesty: that ratio is descriptor
setattr vs **plan apply only** (product ``apply`` uses
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
