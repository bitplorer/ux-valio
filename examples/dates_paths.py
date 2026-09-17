# SPDX-License-Identifier: MIT
"""Date EU/IND parse, pathlib path, IPv4. Slash dates are IND, not US."""

import pathlib
from dataclasses import dataclass
from datetime import date

from ux_valio import DateValidator, IPv4Validator, PathValidator


@dataclass
class Asset:
    opened: date = DateValidator(debug=True, required=True)
    ind_opened: date = DateValidator(debug=True, required=True)
    folder: pathlib.Path = PathValidator(debug=True, required=True)
    host: str = IPv4Validator(debug=True, required=True)


def main() -> Asset:
    row = Asset(
        opened="2020-01-02",
        ind_opened="02/01/2020",
        folder=".",
        host="127.0.0.1",
    )
    assert row.opened == date(2020, 1, 2)
    assert row.ind_opened == date(2020, 1, 2)
    assert row.folder == pathlib.Path(".")
    return row


if __name__ == "__main__":
    print(main())
