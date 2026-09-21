# Host decides, peer applies

Performance map plus the optional product extra. Not a pydantic clone.
The taught API stays ``field: T = SomeValidator(...)``. Stdlib Python is
the default apply. ``pip install ux-valio[native]`` may bind a PyO3
peer for a **closed** plan. That is not a second door (no Field, no
Schema, no BaseModel). Cap Door B is a different stack and is **not**
on this field path.

## Essence

A Python object’s **soul stays on the host**. The instance, the
descriptor, hooks, and exception types are Python. What can leave is a
**compiled plan of specified concerns** plus a **scalar value**. The
peer applies that plan and returns a result. The host decides *whether*
to call, *which* plan, and *how* to raise.

```text
bind / __init__     host compiles specified theory → plan
set                 host hands (plan, value) once
                    peer applies  (int?  ≥ min?)
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
typed failure.” Cap Ops / JSON / ``cek-peer-pyo3`` are not that
channel.

## What the plan is here

The host already compiles at construct:

- ``Validator._active_units`` — specified default-path concerns (type
  always; length/value/pattern/… only when bound)
- uniqueness of ``ValidationPath`` units at ``__init__`` (not per set)

That tuple **is** the plan. Without the extra, the interpreter applies
it. With ``ux-valio[native]``, a **closed** subset is the same tuple as
a native enum, built **once** at ``__init__`` / ``__set_name__``.

Shipped closed plan: ``Integer`` + ``MinValue(i64)`` — the path
``IntegerValidator(min_value=0)`` (and any other i64 ``min_value``).
Unclosed paths (``max_value``, ``required``, ``gt``, named identity,
Email, …) stay on the host. Email / named identity were already
competitive in Python — do not start there.

## What never leaves the host

- ``__set__`` / ``__get__`` / ``__delete__`` (descriptor protocol)
- ``HookHost`` / ``task_*`` / async bridge
- ``AllOf`` / ``AnyOf`` as Python objects (the graph decides; a member
  *may* apply via peer)
- named-facade extras (Luhn, Verhoeff, IBAN, …) until measured
- TypedDict walk, owner annotation honesty, debug-swallow, logger
- ``ValueError`` / ``TypeError`` **wording** — peer returns a small
  error kind; host formats KEEP messages so strings do not fork

## Contract (product extra)

1. Default install has **no** native extra. ``_active_units`` stays the
   apply. ``pip install ux-valio[native]`` installs the ``ux-valio-native``
   wheel (module ``ux_valio_native`` — not a taught import).
2. Same field default. Same ``annotation``. Same fail-closed errors.
   L1 stays ``from ux_valio import IntegerValidator``.
3. Compile at bind, not at set. Missing peer → host apply (no import
   error on the hot path after a failed extra install: bind-time
   choice).
4. One FFI call per set for the specified scalar plan. Not eight.
5. ``self`` is a ``PyObject*`` handle. Do not migrate the instance into
   a Rust struct. Extract scalars (``i64``), apply, box back.
6. Do not re-implement the library in Rust.
7. Do not quote the switch-test ratio as end-to-end product setattr.
   The measure compared full host setattr against **plan apply only**.

From a checkout (needs ``rustc`` / ``cargo``)::

```console
python -m pip install -e .
python -m pip install -e ./native
```

Published extra (when the native wheel is on the index)::

```console
pip install ux-valio[native]
```

Without the extra, every existing test stays on the stdlib path.

## Switch test (why this extra exists)

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
``IntegerValidator(min_value=0)``. Hot path B is ``compile(0)`` once then
``apply(plan, i64)`` on the product peer (``native/``: ``Integer`` +
``MinValue(0)`` only). B is **not** product setattr (no store, no
hooks, no host raise).

```console
python -m pip install -e .
python benches/measure_host_peer.py
python benches/measure_host_peer.py --ci    # never builds Rust; SKIP or smoke
```

Local run needs ``rustc`` / ``cargo`` and will ``pip install maturin``
then ``maturin develop --release`` the peer into the current
interpreter if ``ux_valio_native`` is missing. GitHub Actions has no
Rust toolchain: ``--ci`` (and ``tests/test_host_peer_measure.py``) skip
with that reason, exit 0. Native parity tests
(``tests/test_native_peer.py``) skip without the extra; the rest of
the suite is the stdlib path.

Do not ``from __future__ import annotations`` on the measured ``Box``:
postponed ``int`` TypeErrors at bind (KEEP).

### Measured (2026-09-21)

Same box, two consecutive runs, 400000 iters after 20000 warmup,
values ``(0..7)``, CPython 3.14.7, rustc 1.83.0, Linux x86_64 (Intel
Xeon, 4 CPUs). Peer is a release cdylib. Host units were
``_validate_type`` then ``_validate_value``.

| path | wall (run 1 / 2) | ns/op |
|---|---|---|
| A ``setattr`` ``IntegerValidator(min_value=0)`` | 1.355 s / 1.406 s | 3389 / 3515 |
| B native ``apply(Integer, MinValue(0))`` | 0.0185 s / 0.0186 s | 46.2 / 46.5 |
| host / native | | **73× / 76×** |

Honesty: A is the taught descriptor (``__set__``, specified units, store
on ``instance.__dict__``). B is plan apply only (one FFI, no store, no
hooks). That is the switch the map asked for, **not** a claim that
product setattr is 70× end-to-end after host raise/store. Product
``apply`` releases the GIL (``Python::detach``; PyO3 0.29 name for
``allow_threads``), so a local re-run of B is slower than the stub’s
46 ns/op and still PASSes the 3× bar.

Rename-only re-run on the same box (plan units ``Integer`` +
``MinValue(0)``, same apply): host 3491–3672 ns/op, native 46.8–49.0
ns/op, ratio **75×**. Same PASS.

**Verdict: PASS (native extra shipped for this closed plan).** Host
stayed several times slower than the one-shot native apply (bar 3×).
This extra binds that plan at construct. Cap Door B, JSON-per-set,
migrating ``self`` into Rust, a Field/Schema twin, a mega shared plan
crate, and email/named identity as a first target stay rejected.
