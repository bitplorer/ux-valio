# Performance

Stdlib Python is the apply path today. The taught API does not change
for speed. A native peer is mapped in [host / peer](host-peer-plan.md)
and is **not implemented**.

## What is already compiled

At construct (`Validator.__init__` / `__set_name__`):

- specified default-path units (`_active_units`) — type always; length,
  value, pattern, choice, `reassign`, `multiple_of` only when you passed
  them
- named-facade extra (GSTIN checksum, Luhn, …) as one function after
  that path
- Pattern `re.compile` on the finder

At set, the interpreter walks that short tuple, then process hangs,
then store on `instance.__dict__`, then `post_set` / spawn `task_*`.

Mutating `min_value` after construct does nothing to the path. Pass
bounds at construct.

## What costs on the hot path

| work | when | note |
|---|---|---|
| specified units | every set | the loop you actually want |
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

## What to do in application code

1. Put I/O in `post_validate` (lookup) and `post_set` (persist), not in
   `pre_validate`.
2. Background work is `task_post_set`, then `wait_tasks` at shutdown.
3. Do not wrap every field in `AllOf` of ten leaves if `StringValidator(min_length=3, pattern=…)`
   already specified the path.
4. Ports (`Validator[UserStore]`) run the type door once per construct —
   they are not the bottleneck.
5. `logger=True` is for diagnosis, not production hot paths.
