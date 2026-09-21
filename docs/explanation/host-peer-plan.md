# Host decides, peer applies

Performance map plus a **measure tip**. Not a pydantic clone. The taught
API stays ``field: T = SomeValidator(...)``. Stdlib Python is the
default apply. An optional native peer remains a later extra, never a
second door (no Field, no Schema, no BaseModel). This tree does **not**
ship ``ux-valio[native]`` or Cap Door B.

## Essence

A Python object’s **soul stays on the host**. The instance, the
descriptor, hooks, and exception types are Python. What can leave is a
**compiled plan of specified concerns** plus a **scalar value**. The
peer applies that plan and returns a result. The host decides *whether*
to call, *which* plan, and *how* to raise.

```text
bind / __init__     host compiles specified theory → plan
set                 host hands (plan, value) once
                    peer applies  (int?  ≥ 0?  length?)
                    host stores on instance.__dict__
                    host runs hooks, named extras, debug-swallow
```

One crossing per set. A peer that calls back into Python **per unit**
is slower than today’s path — do not do that.

## Roles (CEK)

| | Host (Python) | Peer (PyO3 / Rust) |
|---|---|---|
| Role | decide | apply |
| Owns | instance, descriptor, hooks, messages | specified scalar plan |
| When | bind, set policy, collect_all, raise | the plan body |
| Lives | always (stdlib) | optional extra |

Host is authority. Peer has no policy: no debug-swallow, no logger, no
``collect_all`` orchestration, no hook dispatch.

This matches a CEK host/peer split: Python host, PyO3 as the apply
peer, communication is “here is the plan and the value; give me ok or a
typed failure.”

## What the plan is here

Today the host already compiles at construct:

- ``Validator._active_units`` — specified default-path concerns (type
  always; length/value/pattern/… only when bound)
- uniqueness of ``ValidationPath`` units at ``__init__`` (not per set)

That tuple **is** the plan, still applied by the Python interpreter.
A peer would be the same tuple as a native enum (``Integer``,
``MinValue``, ``min_length``, compiled regex, choice set, ``multiple_of``,
``reassign``), built **once** at ``__init__`` / ``__set_name__``.

Measured candidate (after the Python compile): unconstrained
``setattr`` of ``int`` is still several Python calls. A native apply of
that one plan is the switch worth considering. Email / named identity
are already competitive in Python — do not start there.

## What never leaves the host

- ``__set__`` / ``__get__`` / ``__delete__`` (descriptor protocol)
- ``HookHost`` / ``task_*`` / async bridge
- ``AllOf`` / ``AnyOf`` as Python objects (the graph decides; a member
  *may* apply via peer)
- named-facade extras (Luhn, Verhoeff, IBAN, …) until measured
- TypedDict walk, owner annotation honesty, debug-swallow, logger
- ``ValueError`` / ``TypeError`` **wording** — peer returns a small
  error kind; host formats KEEP messages so strings do not fork

## Contract if implemented later

1. Default install has **no** native extra. ``_active_units`` stays the
   apply. ``pip install ux-valio[native]`` (name TBD) may bind a peer.
2. Same field default. Same ``annotation``. Same fail-closed errors.
3. Compile at bind, not at set. Missing peer → host apply (no import
   error on the hot path after a failed extra install: bind-time
   choice).
4. One FFI call per set for the specified scalar plan. Not eight.
5. ``self`` is a ``PyObject*`` handle. Do not migrate the instance into
   a Rust struct. Extract scalars (``i64``, ``&str``), apply, box back.
6. Do not re-implement the library in Rust.

## Switch test (when to actually build it)

Build the product peer only if, on the same box, host apply of a
specified ``IntegerValidator(min_value=0)`` setattr stays several times
slower than a one-shot native apply of that same plan, and the Python
compile (``_active_units``, skip TypedDict, skip watch) is already in.

**Bar.** FAIL (KEEP Python) unless host ns/op is **≥ 3×** native ns/op.
Three times is “several”; below that, FFI + a later extra is not worth
the door risk.

### How to run

The harness lives in-tree. It installs/uses ``ux-valio`` from the repo
root. Hot path A is many ``setattr``s on a dataclass ``Box.n`` with
``IntegerValidator(min_value=0)``. Hot path B is ``compile()`` once then
``apply(plan, i64)`` on a **measure-only** PyO3 stub
(``benches/native/``: ``Integer`` + ``MinValue(0)`` only). That stub is not a
published extra.

```console
python -m pip install -e .
python benches/measure_host_peer.py
python benches/measure_host_peer.py --ci    # never builds Rust; SKIP or smoke
```

Local run needs ``rustc`` / ``cargo`` and will ``pip install maturin``
then ``maturin develop --release`` the stub into the current
interpreter. GitHub Actions has no Rust toolchain: ``--ci`` (and
``tests/test_host_peer_measure.py``) skip with that reason, exit 0.

Do not ``from __future__ import annotations`` on the measured ``Box``:
postponed ``int`` TypeErrors at bind (KEEP).

### Measured (2026-09-21)

Same box, two consecutive runs, 400000 iters after 20000 warmup,
values ``(0..7)``, CPython 3.14.7, rustc 1.83.0, Linux x86_64 (Intel
Xeon, 4 CPUs). Stub is a release cdylib. Host units were
``_validate_type`` then ``_validate_value``.

| path | wall (run 1 / 2) | ns/op |
|---|---|---|
| A ``setattr`` ``IntegerValidator(min_value=0)`` | 1.355 s / 1.406 s | 3389 / 3515 |
| B native ``apply(Integer, MinValue(0))`` | 0.0185 s / 0.0186 s | 46.2 / 46.5 |
| host / native | | **73× / 76×** |

Honesty: A is the taught descriptor (``__set__``, specified units, store
on ``instance.__dict__``). B is plan apply only (one FFI, no store, no
hooks). That is the switch the map asked for, not a claim that a product
peer would be 70× end-to-end after host raise/store.

Rename-only re-run on the same box (plan units ``Integer`` +
``MinValue(0)``, same apply): host 3491–3672 ns/op, native 46.8–49.0
ns/op, ratio **75×**. Same PASS.

**Verdict: PASS (native tip unlocked).** Host stayed several times
slower than the one-shot native apply (bar 3×). A later PR may bind an
optional extra. This PR does not. Cap Door B, JSON-per-set, migrating
``self`` into Rust, a Field/Schema twin, a mega shared plan crate, and
email/named identity as a first target stay rejected.
