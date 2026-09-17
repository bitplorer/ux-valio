# SPDX-License-Identifier: MIT
"""Filed document: EU / IND calendar dates, filesystem path, IPv4 host.

``DateValidator`` stores ``datetime.date``. Numeric EU is ``YYYY-MM-DD``;
IND is ``DD-MM-YYYY`` (also ``/`` and ``:``; same delimiter both sides).
``02/01/2020`` is 2 January 2020, not 1 February. ``datetime.datetime`` is
rejected after the inherited path. ``path_exists=True`` requires a real path.
"""

import pathlib
from dataclasses import dataclass
from datetime import date, datetime

from ux_valio import DateValidator, IPv4Validator, PathValidator


@dataclass
class FiledDocument:
    opened_eu: date = DateValidator(debug=True, required=True)
    opened_ind: date = DateValidator(debug=True, required=True)
    folder: pathlib.Path = PathValidator(debug=True, required=True, path_exists=True)
    host: str = IPv4Validator(debug=True, required=True)


def file_document(
    opened_eu: str | date,
    opened_ind: str | date,
    folder: str | pathlib.Path,
    host: str,
) -> FiledDocument:
    """File a document row. Bad dates, missing paths, or hosts raise."""
    return FiledDocument(
        opened_eu=opened_eu,
        opened_ind=opened_ind,
        folder=folder,
        host=host,
    )


def main() -> FiledDocument:
    row = file_document(
        opened_eu="2020-01-02",
        opened_ind="02/01/2020",
        folder=".",
        host="127.0.0.1",
    )
    assert row.opened_eu == date(2020, 1, 2)
    assert row.opened_ind == date(2020, 1, 2)
    assert row.folder == pathlib.Path(".")

    try:
        file_document("2020-13-40", "02/01/2020", ".", "127.0.0.1")
    except ValueError:
        pass
    else:
        raise RuntimeError("invalid calendar date must raise")

    try:
        file_document(datetime(2020, 1, 2), "02/01/2020", ".", "127.0.0.1")
    except TypeError:
        pass
    else:
        raise RuntimeError("datetime.datetime must raise")

    try:
        file_document("2020-01-02", "02/01/2020", ".", "999.0.0.1")
    except ValueError:
        pass
    else:
        raise RuntimeError("invalid IPv4 must raise")

    return row


if __name__ == "__main__":
    filed = main()
    print(f"opened {filed.opened_eu.isoformat()} at {filed.folder} ({filed.host})")
