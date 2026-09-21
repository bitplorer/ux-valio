# SPDX-License-Identifier: MIT
"""Measure host setattr vs a one-shot native apply of Integer + MinValue(0).

Hot path A: many ``setattr``s on a dataclass ``Box`` field with
``IntegerValidator(min_value=0)`` (taught API, soul stays Python).

Hot path B: ``compile()`` once, then ``apply(plan, i64)`` on the
measure-only PyO3 stub under ``benches/native/``. Not a published
``ux-valio[native]`` extra. Not Cap Door B.

Switch bar: FAIL (KEEP Python) unless host ns/op is >= 3× native ns/op.

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
NATIVE_DIR = ROOT / "benches" / "native"
SWITCH_BAR = 3.0
DEFAULT_ITERS = 400_000
DEFAULT_WARMUP = 20_000
VALUES = (0, 1, 2, 3, 4, 5, 6, 7)


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


def _import_stub() -> Any | None:
    try:
        import ux_valio_peer_bench
    except ImportError:
        return None
    return ux_valio_peer_bench


def _build_stub() -> tuple[Any | None, str | None]:
    """Install maturin and build the local cdylib into this interpreter."""
    rustc = shutil.which("rustc")
    cargo = shutil.which("cargo")
    if rustc is None or cargo is None:
        return None, "SKIP: rustc/cargo not on PATH (native stub is local-only)"
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
        return None, f"SKIP: PyO3 stub failed to build ({tail})"
    stub = _import_stub()
    if stub is None:
        return None, "SKIP: stub built but import ux_valio_peer_bench failed"
    return stub, None


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


def _make_box(IntegerValidator: Any) -> Any:
    # Owner annotations must be real types: postponed ``int`` TypeErrors at bind.
    @dataclass
    class Box:
        n: int = IntegerValidator(min_value=0)

    return Box(n=0)


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


def _host_units(IntegerValidator: Any) -> list[str]:
    field = IntegerValidator(min_value=0)
    return [unit.__name__ for unit in field._active_units]


def _smoke(stub: Any) -> str:
    plan = stub.compile()
    ok = stub.apply(plan, 0)
    below = stub.apply(plan, -1)
    if ok is not None:
        raise SystemExit(f"SMOKE FAIL: apply(plan, 0) returned {ok!r}, expected None")
    if below != stub.FailKind.MinValue:
        raise SystemExit(
            f"SMOKE FAIL: apply(plan, -1) returned {below!r}, expected FailKind.MinValue"
        )
    return "SMOKE: compile() + apply(plan, 0) ok; apply(plan, -1) -> FailKind.MinValue"


def _report_header(skip_reason: str | None) -> None:
    rustc = _rustc_version() or "not found"
    print("ux-valio host/peer switch test (measure tip only)")
    print(f"box:      {platform.platform()}")
    print(f"machine:  {platform.machine()}  {platform.processor() or '-'}")
    print(f"python:   {sys.version.split()[0]}  ({sys.executable})")
    print(f"rustc:    {rustc}")
    print("plan:     IntegerValidator(min_value=0)  ==  Integer + MinValue(0)")
    print(f"bar:      FAIL unless host ns/op >= {SWITCH_BAR:.1f}× native ns/op")
    print("scope:    not Cap Door B; not ux-valio[native] product extra")
    if skip_reason:
        print(skip_reason)


def measure(iters: int, warmup: int, stub: Any, IntegerValidator: Any) -> int:
    units = _host_units(IntegerValidator)
    box = _make_box(IntegerValidator)
    host_body = _host_loop(box, VALUES)
    plan = stub.compile()
    native_body = _native_loop(stub.apply, plan, VALUES)

    host_body(warmup)
    native_body(warmup)

    host_ns = _time_loop(iters, host_body)
    native_ns = _time_loop(iters, native_body)
    host_per = host_ns / iters
    native_per = native_ns / iters
    ratio = host_per / native_per if native_per else float("inf")
    unlocked = ratio >= SWITCH_BAR
    verdict = (
        f"PASS (native tip unlocked): host is {ratio:.2f}× native "
        f"(bar {SWITCH_BAR:.1f}×)"
        if unlocked
        else (
            f"FAIL (KEEP Python): host is {ratio:.2f}× native, "
            f"below the {SWITCH_BAR:.1f}× bar"
        )
    )
    print(f"host units: {units}")
    print(f"warmup:   {warmup}   iters: {iters}   values: {VALUES}")
    print("hot path A: setattr Box.n = IntegerValidator(min_value=0)")
    print(f"  {_fmt_ns(host_ns, iters)}")
    print("hot path B: native apply(plan, i64)  [Integer + MinValue(0)]")
    print(f"  {_fmt_ns(native_ns, iters)}")
    print(f"ratio:    host/native = {ratio:.2f}")
    print(f"VERDICT:  {verdict}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure IntegerValidator setattr vs native Integer+MinValue(0) apply."
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Never build Rust. Smoke if the stub is already importable; else skip.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not try maturin develop when the stub is missing.",
    )
    parser.add_argument("--iters", type=int, default=DEFAULT_ITERS)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP)
    args = parser.parse_args(argv)

    IntegerValidator = _load_ux_valio()
    stub = _import_stub()
    skip_reason: str | None = None
    if stub is None and not args.ci and not args.skip_build:
        stub, skip_reason = _build_stub()
    elif stub is None and args.ci:
        skip_reason = (
            "SKIP: native stub not built (CI has no Rust/PyO3 toolchain; "
            "run locally: python benches/measure_host_peer.py)"
        )
    elif stub is None:
        skip_reason = "SKIP: ux_valio_peer_bench is not importable and build was skipped"

    _report_header(skip_reason if stub is None else None)
    if stub is None:
        return 0
    print(_smoke(stub))
    if args.ci:
        print("CI: smoke only (full wall-clock measure is local)")
        return 0
    if args.iters < 1:
        raise SystemExit("--iters must be >= 1")
    if args.warmup < 0:
        raise SystemExit("--warmup must be >= 0")
    return measure(args.iters, args.warmup, stub, IntegerValidator)


if __name__ == "__main__":
    raise SystemExit(main())
