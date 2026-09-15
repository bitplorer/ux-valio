# SPDX-License-Identifier: MIT
"""Collected validation failures from collect_all=True.

Default Door A stays fail-fast. collect_all is not debug-swallow.
"""

from __future__ import annotations

from typing import Any


class ValidationErrors(ValueError):
    """Every concern that failed when ``collect_all=True``."""

    def __init__(self, errors: list[BaseException], name: Any = None) -> None:
        if not errors:
            raise ValueError("ValidationErrors requires at least one error")
        self.errors = list(errors)
        label = name if name is not None else "value"
        joined = "; ".join(str(err) for err in self.errors)
        n = len(self.errors)
        super().__init__(
            f"{label} failed {n} check{'s' if n != 1 else ''}: {joined}"
        )


def continue_or_raise(
    collect_all: bool, errors: list[BaseException], err: BaseException
) -> None:
    if not collect_all:
        raise err
    if isinstance(err, ValidationErrors):
        errors.extend(err.errors)
    else:
        errors.append(err)


def raise_collected(errors: list[BaseException], name: Any = None) -> None:
    if errors:
        raise ValidationErrors(errors, name=name)
