# SPDX-License-Identifier: MIT
"""Measure host setattr vs one-shot native apply of Integer/Float/String/Bytes plans.

Hot path A: many ``setattr``s on a dataclass ``Box`` field with a closed
``IntegerValidator`` / ``FloatValidator`` bound plan or closed
``StringValidator`` / ``BytesValidator`` length plan (taught API, soul
stays Python).

Hot path B: ``compile(...)`` / ``compile_float(...)`` /
``compile_string(...)`` / ``compile_bytes(...)`` once, then ``apply`` /
``apply_float`` / ``apply_string`` / ``apply_bytes`` on the
``ux_valio_native`` peer. That is
plan apply only — not a claim that product setattr is 70× after host
store/raise. Not Cap Door B.

Families: MinValue, MaxValue, GreaterThan, LessThan, Equal, min+max
range — once for Integer, once for Float — plus String and Bytes
MinLength / MaxLength / Length / min+max range. Switch bar:
FAIL (KEEP Python) unless host ns/op is >= 3× native ns/op. A family
below the bar is not claimed native (KEEP host for that family).
Next HOLD: IntegerEnum, then StringEnum.

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
PASSING_0_7_F = (0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)
PASSING_1_8_F = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0)
PASSING_EQ_F = (7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0, 7.0)
PASSING_A_H = ("a", "b", "c", "d", "e", "f", "g", "h")
PASSING_LEN3 = ("abc", "abc", "abc", "abc", "abc", "abc", "abc", "abc")
PASSING_A_H_B = (b"a", b"b", b"c", b"d", b"e", b"f", b"g", b"h")
PASSING_LEN3_B = (b"abc", b"abc", b"abc", b"abc", b"abc", b"abc", b"abc", b"abc")


@dataclass(frozen=True)
class PlanFamily:
    name: str
    facade: str
    compile_attr: str
    apply_attr: str
    annotation: type
    field_kwargs: dict[str, Any]
    compile_kwargs: dict[str, Any]
    values: tuple[Any, ...]
    seed: Any
    smoke_ok: Any
    smoke_miss: Any
    smoke_kind: str
    label: str


def _integer_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="IntegerValidator",
        compile_attr="compile",
        apply_attr="apply",
        annotation=int,
        **kwargs,
    )


def _float_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="FloatValidator",
        compile_attr="compile_float",
        apply_attr="apply_float",
        annotation=float,
        **kwargs,
    )


def _string_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="StringValidator",
        compile_attr="compile_string",
        apply_attr="apply_string",
        annotation=str,
        **kwargs,
    )


def _bytes_family(**kwargs: Any) -> PlanFamily:
    return PlanFamily(
        facade="BytesValidator",
        compile_attr="compile_bytes",
        apply_attr="apply_bytes",
        annotation=bytes,
        **kwargs,
    )


INTEGER_FAMILIES = (
    _integer_family(
        name="Integer.MinValue",
        field_kwargs={"min_value": 0},
        compile_kwargs={"min_value": 0},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=5,
        smoke_miss=-1,
        smoke_kind="MinValue",
        label="Integer + MinValue(0)",
    ),
    _integer_family(
        name="Integer.MaxValue",
        field_kwargs={"max_value": 10},
        compile_kwargs={"max_value": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=10,
        smoke_miss=11,
        smoke_kind="MaxValue",
        label="Integer + MaxValue(10)",
    ),
    _integer_family(
        name="Integer.GreaterThan",
        field_kwargs={"gt": 0},
        compile_kwargs={"gt": 0},
        values=PASSING_1_8,
        seed=1,
        smoke_ok=1,
        smoke_miss=0,
        smoke_kind="GreaterThan",
        label="Integer + GreaterThan(0)",
    ),
    _integer_family(
        name="Integer.LessThan",
        field_kwargs={"lt": 10},
        compile_kwargs={"lt": 10},
        values=PASSING_0_7,
        seed=0,
        smoke_ok=9,
        smoke_miss=10,
        smoke_kind="LessThan",
        label="Integer + LessThan(10)",
    ),
    _integer_family(
        name="Integer.Equal",
        field_kwargs={"eq": 7},
        compile_kwargs={"eq": 7},
        values=PASSING_EQ,
        seed=7,
        smoke_ok=7,
        smoke_miss=8,
        smoke_kind="Equal",
        label="Integer + Equal(7)",
    ),
    _integer_family(
        name="Integer.Range",
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

FLOAT_FAMILIES = (
    _float_family(
        name="Float.MinValue",
        field_kwargs={"min_value": 0.0},
        compile_kwargs={"min_value": 0.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=5.0,
        smoke_miss=-1.0,
        smoke_kind="MinValue",
        label="Float + MinValue(0.0)",
    ),
    _float_family(
        name="Float.MaxValue",
        field_kwargs={"max_value": 10.0},
        compile_kwargs={"max_value": 10.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=10.0,
        smoke_miss=11.0,
        smoke_kind="MaxValue",
        label="Float + MaxValue(10.0)",
    ),
    _float_family(
        name="Float.GreaterThan",
        field_kwargs={"gt": 0.0},
        compile_kwargs={"gt": 0.0},
        values=PASSING_1_8_F,
        seed=1.0,
        smoke_ok=1.0,
        smoke_miss=0.0,
        smoke_kind="GreaterThan",
        label="Float + GreaterThan(0.0)",
    ),
    _float_family(
        name="Float.LessThan",
        field_kwargs={"lt": 10.0},
        compile_kwargs={"lt": 10.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=9.0,
        smoke_miss=10.0,
        smoke_kind="LessThan",
        label="Float + LessThan(10.0)",
    ),
    _float_family(
        name="Float.Equal",
        field_kwargs={"eq": 7.0},
        compile_kwargs={"eq": 7.0},
        values=PASSING_EQ_F,
        seed=7.0,
        smoke_ok=7.0,
        smoke_miss=8.0,
        smoke_kind="Equal",
        label="Float + Equal(7.0)",
    ),
    _float_family(
        name="Float.Range",
        field_kwargs={"min_value": 0.0, "max_value": 10.0},
        compile_kwargs={"min_value": 0.0, "max_value": 10.0},
        values=PASSING_0_7_F,
        seed=0.0,
        smoke_ok=5.0,
        smoke_miss=-1.0,
        smoke_kind="MinValue",
        label="Float + MinValue(0.0) + MaxValue(10.0)",
    ),
)

STRING_FAMILIES = (
    _string_family(
        name="String.MinLength",
        field_kwargs={"min_length": 1},
        compile_kwargs={"min_length": 1},
        values=PASSING_A_H,
        seed="a",
        smoke_ok="a",
        smoke_miss="",
        smoke_kind="MinLength",
        label="String + MinLength(1)",
    ),
    _string_family(
        name="String.MaxLength",
        field_kwargs={"max_length": 10},
        compile_kwargs={"max_length": 10},
        values=PASSING_A_H,
        seed="a",
        smoke_ok="a",
        smoke_miss="abcdefghijk",
        smoke_kind="MaxLength",
        label="String + MaxLength(10)",
    ),
    _string_family(
        name="String.Length",
        field_kwargs={"length": 3},
        compile_kwargs={"length": 3},
        values=PASSING_LEN3,
        seed="abc",
        smoke_ok="abc",
        smoke_miss="ab",
        smoke_kind="Length",
        label="String + Length(3)",
    ),
    _string_family(
        name="String.Range",
        field_kwargs={"min_length": 1, "max_length": 10},
        compile_kwargs={"min_length": 1, "max_length": 10},
        values=PASSING_A_H,
        seed="a",
        smoke_ok="a",
        smoke_miss="",
        smoke_kind="MinLength",
        label="String + MinLength(1) + MaxLength(10)",
    ),
)

BYTES_FAMILIES = (
    _bytes_family(
        name="Bytes.MinLength",
        field_kwargs={"min_length": 1},
        compile_kwargs={"min_length": 1},
        values=PASSING_A_H_B,
        seed=b"a",
        smoke_ok=b"a",
        smoke_miss=b"",
        smoke_kind="MinLength",
        label="Bytes + MinLength(1)",
    ),
    _bytes_family(
        name="Bytes.MaxLength",
        field_kwargs={"max_length": 10},
        compile_kwargs={"max_length": 10},
        values=PASSING_A_H_B,
        seed=b"a",
        smoke_ok=b"a",
        smoke_miss=b"abcdefghijk",
        smoke_kind="MaxLength",
        label="Bytes + MaxLength(10)",
    ),
    _bytes_family(
        name="Bytes.Length",
        field_kwargs={"length": 3},
        compile_kwargs={"length": 3},
        values=PASSING_LEN3_B,
        seed=b"abc",
        smoke_ok=b"abc",
        smoke_miss=b"ab",
        smoke_kind="Length",
        label="Bytes + Length(3)",
    ),
    _bytes_family(
        name="Bytes.Range",
        field_kwargs={"min_length": 1, "max_length": 10},
        compile_kwargs={"min_length": 1, "max_length": 10},
        values=PASSING_A_H_B,
        seed=b"a",
        smoke_ok=b"a",
        smoke_miss=b"",
        smoke_kind="MinLength",
        label="Bytes + MinLength(1) + MaxLength(10)",
    ),
)

FAMILIES = INTEGER_FAMILIES + FLOAT_FAMILIES + STRING_FAMILIES + BYTES_FAMILIES


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


def _load_facades() -> dict[str, Any]:
    _ensure_tree_on_path()
    try:
        from ux_valio import (
            BytesValidator,
            FloatValidator,
            IntegerValidator,
            StringValidator,
        )
    except ImportError as err:
        raise SystemExit(
            "FAIL: ux-valio is not importable from the tree. "
            f"Install with `{sys.executable} -m pip install -e .` ({err})"
        ) from err
    return {
        "IntegerValidator": IntegerValidator,
        "FloatValidator": FloatValidator,
        "StringValidator": StringValidator,
        "BytesValidator": BytesValidator,
    }


def _make_box(facades: dict[str, Any], family: PlanFamily) -> Any:
    # Owner annotations must be real types: postponed ``int`` TypeErrors at bind.
    # Force stdlib apply on path A so the switch still compares host units vs
    # plan-apply-only (product setattr is host+store+raise, not this bar).
    from ux_valio.validators._native import _clear_native

    facade = facades[family.facade]
    field = facade(**family.field_kwargs)
    _clear_native(field)
    seed = family.seed
    if family.annotation is bytes:

        @dataclass
        class BytesBox:
            n: bytes = field

        return BytesBox(n=seed)
    if family.annotation is str:

        @dataclass
        class StrBox:
            n: str = field

        return StrBox(n=seed)
    if family.annotation is float:

        @dataclass
        class FloatBox:
            n: float = field

        return FloatBox(n=seed)

    @dataclass
    class IntBox:
        n: int = field

    return IntBox(n=seed)


def _time_loop(n: int, body: Any) -> int:
    start = time.perf_counter_ns()
    body(n)
    return time.perf_counter_ns() - start


def _host_loop(box: Any, values: tuple[Any, ...]) -> Any:
    mask = len(values) - 1
    name = "n"
    set_attr = setattr

    def run(n: int) -> None:
        for i in range(n):
            set_attr(box, name, values[i & mask])

    return run


def _native_loop(apply: Any, plan: Any, values: tuple[Any, ...]) -> Any:
    mask = len(values) - 1

    def run(n: int) -> None:
        for i in range(n):
            apply(plan, values[i & mask])

    return run


def _fmt_ns(total_ns: int, n: int) -> str:
    per = total_ns / n
    seconds = total_ns / 1_000_000_000
    return f"{seconds:.6f} s   {per:.1f} ns/op"


def _host_units(facades: dict[str, Any], family: PlanFamily) -> list[str]:
    field = facades[family.facade](**family.field_kwargs)
    return [unit.__name__ for unit in field._active_units]


def _smoke_family(peer: Any, family: PlanFamily) -> str:
    compile_fn = getattr(peer, family.compile_attr)
    apply_fn = getattr(peer, family.apply_attr)
    plan = compile_fn(**family.compile_kwargs)
    ok = apply_fn(plan, family.smoke_ok)
    miss = apply_fn(plan, family.smoke_miss)
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
        f"SMOKE: {family.name}: {family.compile_attr}({family.compile_kwargs}) "
        f"+ {family.apply_attr}({family.smoke_ok}) ok; {family.apply_attr}("
        f"{family.smoke_miss}) -> FailKind.{family.smoke_kind}"
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
    print(
        "plan:     Integer i64 + Float f64 bound units "
        "(MinValue/MaxValue/GreaterThan/LessThan/Equal/range); "
        "String length units (MinLength/MaxLength/Length/range, codepoints); "
        "Bytes length units (MinLength/MaxLength/Length/range, byte count)"
    )
    print(f"bar:      FAIL unless host ns/op >= {SWITCH_BAR:.1f}× native ns/op")
    print("scope:    not Cap Door B; B is plan-apply-only (not 70× product setattr)")
    if skip_reason:
        print(skip_reason)


def _measure_family(
    iters: int,
    warmup: int,
    peer: Any,
    facades: dict[str, Any],
    family: PlanFamily,
) -> tuple[bool, float, float, float]:
    units = _host_units(facades, family)
    box = _make_box(facades, family)
    host_body = _host_loop(box, family.values)
    compile_fn = getattr(peer, family.compile_attr)
    apply_fn = getattr(peer, family.apply_attr)
    plan = compile_fn(**family.compile_kwargs)
    native_body = _native_loop(apply_fn, plan, family.values)

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
    print(f"hot path A: setattr Box.n = {family.facade}({family.field_kwargs})")
    print(f"  {_fmt_ns(host_ns, iters)}")
    print(f"hot path B: native {family.apply_attr}(plan, scalar)  [{family.label}]")
    print(f"  {_fmt_ns(native_ns, iters)}")
    print(f"ratio:    host/native = {ratio:.2f}")
    print(f"VERDICT:  {verdict}")
    print()
    return unlocked, ratio, host_per, native_per


def measure(iters: int, warmup: int, peer: Any, facades: dict[str, Any]) -> int:
    results: list[tuple[PlanFamily, bool, float]] = []
    for family in FAMILIES:
        unlocked, ratio, _host_per, _native_per = _measure_family(
            iters, warmup, peer, facades, family
        )
        results.append((family, unlocked, ratio))
    integer = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "IntegerValidator"]
    floating = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "FloatValidator"]
    string = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "StringValidator"]
    blob = [(family, unlocked, ratio) for family, unlocked, ratio in results if family.facade == "BytesValidator"]
    failed = [family.name for family, unlocked, _ratio in results if not unlocked]
    int_passed = [family.name for family, unlocked, _ratio in integer if unlocked]
    int_new = [name for name in int_passed if name != "Integer.MinValue"]
    float_failed = [family.name for family, unlocked, _ratio in floating if not unlocked]
    float_passed = [family.name for family, unlocked, _ratio in floating if unlocked]
    string_failed = [family.name for family, unlocked, _ratio in string if not unlocked]
    string_passed = [family.name for family, unlocked, _ratio in string if unlocked]
    bytes_failed = [family.name for family, unlocked, _ratio in blob if not unlocked]
    bytes_passed = [family.name for family, unlocked, _ratio in blob if unlocked]
    if any(not unlocked for _family, unlocked, _ratio in integer):
        print(
            f"SUMMARY: FAIL (KEEP Python) Integer families below {SWITCH_BAR:.1f}×: "
            + ", ".join(name for name in failed if name.startswith("Integer."))
        )
        return 1
    if not int_new:
        print(
            "SUMMARY: SKIP honestly — Integer MinValue met the bar but no new "
            "Integer family (MaxValue/GreaterThan/LessThan/Equal/Range) did"
        )
        return 0
    if float_failed:
        print(
            f"SUMMARY: Float KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(float_failed)
            + ". Do not claim native for those families. "
            + (
                f"Float native unlocked: {', '.join(float_passed)}"
                if float_passed
                else "No Float family met the bar."
            )
        )
        return 1
    if string_failed:
        print(
            f"SUMMARY: String KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(string_failed)
            + ". Do not claim native for those families. "
            + (
                f"String native unlocked: {', '.join(string_passed)}"
                if string_passed
                else "No String family met the bar."
            )
        )
        return 1
    if bytes_failed:
        print(
            f"SUMMARY: Bytes KEEP host (below {SWITCH_BAR:.1f}×): "
            + ", ".join(bytes_failed)
            + ". Do not claim native for those families. IntegerEnum is next. "
            + (
                f"Bytes native unlocked: {', '.join(bytes_passed)}"
                if bytes_passed
                else "No Bytes family met the bar."
            )
        )
        return 1
    print(
        f"SUMMARY: PASS — {', '.join(int_passed + float_passed + string_passed + bytes_passed)} each >= "
        f"{SWITCH_BAR:.1f}× (plan-apply-only; not 70× product setattr)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Measure IntegerValidator/FloatValidator/StringValidator/"
            "BytesValidator setattr vs native bound/length-plan apply."
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

    facades = _load_facades()
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
    return measure(args.iters, args.warmup, peer, facades)


if __name__ == "__main__":
    raise SystemExit(main())
