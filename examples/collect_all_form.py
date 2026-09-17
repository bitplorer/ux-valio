# SPDX-License-Identifier: MIT
"""collect_all=True continues remaining concerns and surfaces ValidationErrors."""

from dataclasses import dataclass

import pytest

from ux_valio import IntegerValidator, ValidationErrors


@dataclass
class ScoreCard:
    n: int = IntegerValidator(
        min_value=0, max_value=10, multiple_of=2, collect_all=True, debug=True
    )


def main() -> None:
    ok = ScoreCard(n=8)
    assert ok.n == 8
    with pytest.raises(ValidationErrors):
        ScoreCard(n=7)
    with pytest.raises(ValidationErrors):
        ScoreCard(n=-3)


if __name__ == "__main__":
    main()
    print("collect_all examples ok")
