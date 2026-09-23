# SPDX-License-Identifier: MIT
"""Product setattr for a closed native int. Not the host/peer switch test.

The switch test in ``measure_host_peer.py`` compares descriptor setattr
with one-shot ``apply_integer``. This script times the taught setattr
only (store included). It does not claim that ratio.

Usage::

    python benches/measure_product_setattr.py
"""

import time
from dataclasses import dataclass

from ux_valio import IntegerValidator


WARMUP = 4_000
ROUNDS = 7
ITERS = 80_000


def _median_us(body) -> float:
    for _ in range(WARMUP):
        body()
    samples: list[float] = []
    for _ in range(ROUNDS):
        start = time.perf_counter_ns()
        for _i in range(ITERS):
            body()
        samples.append((time.perf_counter_ns() - start) / ITERS / 1_000)
    samples.sort()
    return samples[len(samples) // 2]


def main() -> None:
    @dataclass
    class Bare:
        n: int = IntegerValidator(min_value=0)

    bare = Bare(n=1)

    def set_bare() -> None:
        bare.n = 3

    @dataclass
    class EmptyHangs:
        n: int = IntegerValidator(min_value=0)

        @n.pre_validate
        def pre(self, value):
            return value

        @n.post_validate
        def post(self, value):
            return value

    empty = EmptyHangs(n=1)

    def set_empty() -> None:
        empty.n = 3

    @dataclass
    class Thin:
        n: int = IntegerValidator(min_value=0)

        @n.pre_validate
        def pre(self, value):
            return 0 if value is None else value

        @n.post_validate
        def post(self, value):
            return value

    thin = Thin(n=1)

    def set_thin() -> None:
        thin.n = 3

    print(f"no hangs:        {_median_us(set_bare):.3f} µs")
    print(f"empty pre+post:  {_median_us(set_empty):.3f} µs")
    print(f"thin pre+post:   {_median_us(set_thin):.3f} µs")


if __name__ == "__main__":
    main()
