# SPDX-License-Identifier: MIT
"""Measure host setattr vs one-shot native apply of Integer bound plans.

Hot path A: many ``setattr``s on a dataclass ``Box`` field with a closed
``IntegerValidator`` bound plan (taught API, soul stays Python).

Hot path B: ``compile(...)`` once, then ``apply(plan, i64)`` on the
``ux-valio[native]`` peer. That is plan apply only — not a claim that
product setattr is 70× after host store/raise. Not Cap Door B.

Families: MinValue, MaxValue, Gt, Lt, Eq, min+max range. Switch bar:
FAIL (KEEP Python) unless host ns/op is >= 3× native ns/op. At least
one family besides MinValue must meet the bar, or SKIP honestly.

Usage::

    python benches/measure_host_peer.py
    python benches/measure_host_peer.py --ci
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NATIVE_DIR = ROOT / "native"
SWITCH_BAR = 3.0
DEFAULT_ITERS = 400_000
DEFAULT_WARMUP = 20_000
PASSING_0_7 = (0, 1, 2, 3, 4, 5, 6, 7)
PASSING_1_8 = (1, 2, 3, 4, 5, 6, 7, 8)
PASSING_EQ = (7, 7, 7, 7, 7, 7, 7, 7)


@dataclass(frozen=True)
class PlanFamily:
    name: str
    field_kwargs: dict[str, int]
    compile_kwargs: dict[str, int]
    values: tuple[int, ...]
    seed: int
    smoke_ok: int
    smoke_miss: int
    smoke_kind: str
    label: str


FAMILIES = (
    PlanFamily(
        name="MinValue",
        field_kwargs={"min_value": 0},
        compile_kwargs={"min_value": 0},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=5,
        smoke_miss=4,
        smoke_kind="MinValue",
        label="Integer + MinValue(0)",
    ),
    PlanFamily(
        name="MaxValue",
        field_kwargs={"max_value": 10},
        compile_kwargs={"max_value": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=10,
        smoke_miss=11,
        smoke_kind="MaxValue",
        label="Integer + MaxValue(10)",
    ),
    PlanFamily(
        name="Gt",
        field_kwargs={"gt": 0},
        compile_kwargs={"gt": 0},
        values=PASSING_1_8,
        seed=1,
        smoke_ok=1,
        smoke_miss=0,
        smoke_kind="Gt",
        label="Integer + Gt(0)",
    ),
    PlanFamily(
        name="Lt",
        field_kwargs={"lt": 10},
        compile_kwargs={"lt": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=9,
        smoke_miss=10,
        smoke_kind="Lt",
        label="Integer + Lt(10)",
    ),
    PlanFamily(
        name="Eq",
        field_kwargs={"eq": 7},
        compile_kwargs={"eq": 7},
        values=PASSING_EQ,
        seed=7,
        smoke_ok=7,
        smoke_miss=8,
        smoke_kind="Eq",
        label="Integer + Eq(7)",
    ),
    PlanFamily(
        name="Range",
        field_kwargs={"min_value": 0, "max_value": 10},
        compile_kwargs={"min_value": 0, "max_value": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=5,
        smoke_miss=-1,
        smoke_kind="MinValue",
        label="Integer + MinValue(0) + MaxValue(10)",
    ),
)


def _ensure_tree_on_path() -> None:
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        capture_output=True,
        **kwargs,
    )


def _python_cmd() -> list[str]:
    return [sys.executable]


def _rustc_version() -> str | None:
    rustc = shutil.which("rustc")
    if rustc is None:
        return None
    proc = _run([rustc, "--version"])
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or proc.stderr.strip() or None


def _import_peer() -> Any | None:
    try:
        import ux_valio_native
    except ImportError:
        return None
    return ux_valio_native


def _build_peer() -> tuple[Any | None, str | None]:
    """Install maturin and build the local cdylib into this interpreter."""
    rustc = shutil.which("rustc")
    cargo = shutil.which("cargo")
    if rustc is None or cargo is None:
        return None, "SKIP: rustc/cargo not on PATH (native extra is local-only)"
    pip = _run(
        [*_python_cmd(), "-m", "pip", "install", "-q", "maturin>=1.7,<2"],
        cwd=str(ROOT),
    )
    if pip.returncode != 0:
        detail = (pip.stderr or pip.stdout).strip().splitlines()
        tail = detail[-1] if detail else "pip install maturin failed"
        return None, f"SKIP: could not install maturin ({tail})"
    env = os.environ.copy()
    env.setdefault("CARGO_TERM_COLOR", "never")
    built = _run(
        [
            *_python_cmd(),
            "-m",
            "maturin",
            "develop",
            "--release",
            "--manifest-path",
            str(NATIVE_DIR / "Cargo.toml"),
        ],
        cwd=str(NATIVE_DIR),
        env=env,
    )
    if built.returncode != 0:
        detail = (built.stderr or built.stdout).strip().splitlines()
        tail = detail[-1] if detail else "maturin develop failed"
        return None, f"SKIP: native peer failed to build ({tail})"
    peer = _import_peer()
    if peer is None:
        return None, "SKIP: peer built but import ux_valio_native failed"
    return peer, None


def _load_ux_valio() -> Any:
    _ensure_tree_on_path()
    try:
        from ux_valio import IntegerValidator
    except ImportError as err:
        raise SystemExit(
            "FAIL: ux-valio is not importable from the tree. "
            f"Install with `{sys.executable} -m pip install -e .` ({err})"
        ) from err
    return IntegerValidator


def _make_box(IntegerValidator: Any, family: PlanFamily) -> Any:
    # Owner annotations must be real types: postponed ``int`` TypeErrors at bind.
    # Force stdlib apply on path A so the switch still compares host units vs
    # plan-apply-only (product setattr is host+store+raise, not this bar).
    from ux_valio.validators._native import _clear_native

    field = IntegerValidator(**family.field_kwargs)
    _clear_native(field)
    seed = family.seed

    @dataclass
    class Box:
        n: int = field

    return Box(n=seed)


def _time_loop(n: int, body: Any) -> int:
    start = time.perf_counter_ns()
    body(n)
    return time.perf_counter_ns() - start


def _host_loop(box: Any, values: tuple[int, ...]) -> Any:
    mask = len(values) - 1
    name = "n"
    set_attr = setattr

    def run(n: int) -> None:
        for i in range(n):
            set_attr(box, name, values[i & mask])

    return run


def _native_loop(apply: Any, plan: Any, values: tuple[int, ...]) -> Any:
    mask = len(values) - 1

    def run(n: int) -> None:
        for i in range(n):
            apply(plan, values[i & mask])

    return run


def _fmt_ns(total_ns: int, n: int) -> str:
    per = total_ns / n
    seconds = total_ns / 1_000_000_000
    return f"{seconds:.6f} s   {per:.1f} ns/op"


def _host_units(IntegerValidator: Any, family: PlanFamily) -> list[str]:
    field = IntegerValidator(**family.field_kwargs)
    return [unit.__name__ for unit in field._active_units]


def _smoke_family(peer: Any, family: PlanFamily) -> str:
    plan = peer.compile(**family.compile_kwargs)
    ok = peer.apply(plan, family.smoke_ok)
    miss = peer.apply(plan, family.smoke_miss)
    kind = getattr(peer.FailKind, family.smoke_kind)
    if ok is not None:
        raise SystemExit(
            f"SMOKE FAIL {family.name}: apply(plan, {family.smoke_ok}) "
            f"returned {ok!r}, expected None"
        )
    if miss != kind:
        raise SystemExit(
            f"SMOKE FAIL {family.name}: apply(plan, {family.smoke_miss}) "
            f"returned {miss!r}, expected FailKind.{family.smoke_kind}"
        )
    return (
        f"SMOKE {family.name}: compile({family.compile_kwargs}) "
        f"+ apply({family.smoke_ok}) ok; apply({family.smoke_miss}) "
        f"-> FailKind.{family.smoke_kind}"
    )


def _smoke(peer: Any) -> str:
    lines = [_smoke_family(peer, family) for family in FAMILIES]
    return "\n".join(lines)


def _report_header(skip_reason: str | None) -> None:
    rustc = _rustc_version() or "not found"
    print("ux-valio host/peer switch test")
    print(f"box:      {platform.platform()}")
    print(f"machine:  {platform.machine()}  {platform.processor() or '-'}")
    print(f"python:   {sys.version.split()[0]}  ({sys.executable})")
    print(f"rustc:    {rustc}")
    print("plan:     Integer bound units (MinValue/MaxValue/Gt/Lt/Eq/range)")
    print(f"bar:      FAIL unless host ns/op >= {SWITCH_BAR:.1f}× native ns/op")
    print("scope:    not Cap Door B; B is plan-apply-only (not 70× product setattr)")
    if skip_reason:
        print(skip_reason)


def _measure_family(
    iters: int,
    warmup: int,
    peer: Any,
    IntegerValidator: Any,
    family: PlanFamily,
) -> tuple[bool, float]:
    units = _host_units(IntegerValidator, family)
    box = _make_box(IntegerValidator, family)
    host_body = _host_loop(box, family.values)
    plan = peer.compile(**family.compile_kwargs)
    native_body = _native_loop(peer.apply, plan, family.values)

    host_body(warmup)
    native_body(warmup)

    host_ns = _time_loop(iters, host_body)
    native_ns = _time_loop(iters, native_body)
    host_per = host_ns / iters
    native_per = native_ns / iters
    ratio = host_per / native_per if native_per else float("inf")
    unlocked = ratio >= SWITCH_BAR
    verdict = (
        f"PASS (native extra unlocked): host is {ratio:.2f}× native "
        f"(bar {SWITCH_BAR:.1f}×)"
        if unlocked
        else (
            f"FAIL (KEEP Python): host is {ratio:.2f}× native, "
            f"below the {SWITCH_BAR:.1f}× bar"
        )
    )
    print(f"family:   {family.name}  [{family.label}]")
    print(f"host units: {units}")
    print(f"warmup:   {warmup}   iters: {iters}   values: {family.values}")
    print(f"hot path A: setattr Box.n = IntegerValidator({family.field_kwargs})")
    print(f"  {_fmt_ns(host_ns, iters)}")
    print(f"hot path B: native apply(plan, i64)  [{family.label}]")
    print(f"  {_fmt_ns(native_ns, iters)}")
    print(f"ratio:    host/native = {ratio:.2f}")
    print(f"VERDICT:  {verdict}")
    print()
    return unlocked, ratio


def measure(iters: int, warmup: int, peer: Any, IntegerValidator: Any) -> int:
    results: list[tuple[PlanFamily, bool, float]] = []
    for family in FAMILIES:
        unlocked, ratio = _measure_family(
            iters, warmup, peer, IntegerValidator, family
        )
        results.append((family, unlocked, ratio))
    passed = [family.name for family, unlocked, _ratio in results if unlocked]
    failed = [family.name for family, unlocked, _ratio in results if not unlocked]
    new_passed = [name for name in passed if name != "MinValue"]
    if failed:
        print(
            f"SUMMARY: FAIL (KEEP Python) families below {SWITCH_BAR:.1f}×: "
            + ", ".join(failed)
        )
        return 1
    if not new_passed:
        print(
            "SUMMARY: SKIP honestly — MinValue met the bar but no new "
            "family (Max/Gt/Lt/Eq/Range) did"
        )
        return 0
    print(
        f"SUMMARY: PASS — {', '.join(passed)} each >= {SWITCH_BAR:.1f}× "
        "(plan-apply-only; not 70× product setattr)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Measure IntegerValidator setattr vs native Integer bound-plan apply."
        )
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Never build Rust. Smoke if the peer is already importable; else skip.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not try maturin develop when the peer is missing.",
    )
    parser.add_argument("--iters", type=int, default=DEFAULT_ITERS)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP)
    args = parser.parse_args(argv)

    IntegerValidator = _load_ux_valio()
    peer = _import_peer()
    skip_reason: str | None = None
    if peer is None and not args.ci and not args.skip_build:
        peer, skip_reason = _build_peer()
    elif peer is None and args.ci:
        skip_reason = (
            "SKIP: native peer not built (CI has no Rust/PyO3 toolchain; "
            "run locally: python benches/measure_host_peer.py)"
        )
    elif peer is None:
        skip_reason = "SKIP: ux_valio_native is not importable and build was skipped"

    _report_header(skip_reason if peer is None else None)
    if peer is None:
        return 0
    print(_smoke(peer))
    if args.ci:
        print("CI: smoke only (full wall-clock measure is local)")
        return 0
    if args.iters < 1:
        raise SystemExit("--iters must be >= 1")
    if args.warmup < 0:
        raise SystemExit("--warmup must be >= 0")
    return measure(args.iters, args.warmup, peer, IntegerValidator)


if __name__ == "__main__":
    raise SystemExit(main())
