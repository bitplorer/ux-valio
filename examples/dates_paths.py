# SPDX-License-Identifier: MIT
"""File a document: EU / IND dates, existing folder, IPv4 host, archive port.

``DateValidator`` stores ``datetime.date``. ``02/01/2020`` is 2 January 2020,
not 1 February. ``path_exists=True`` requires a real path. Inject ``Archive``
on ``FilingService``.
"""

import pathlib
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from ux_valio import DateValidator, IPv4Validator, PathValidator


class Archive(Protocol):
    """Already-filed folder+host. Production: unique (folder, host) in the archive."""

    def already_filed(self, folder: pathlib.Path, host: str) -> bool:
        """True when this folder has already been filed from ``host``."""
        ...

    def commit(self, folder: pathlib.Path, host: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryArchive:
    """Runnable fake. Plug in object storage that satisfies ``Archive``."""

    def __init__(self, filed: set[tuple[str, str]] | None = None) -> None:
        self._filed = set(filed or ())

    def already_filed(self, folder: pathlib.Path, host: str) -> bool:
        return (str(folder), host) in self._filed

    def commit(self, folder: pathlib.Path, host: str) -> None:
        self._filed.add((str(folder), host))


@dataclass
class FiledDocument:
    archive: Archive
    opened_eu: date = DateValidator(required=True)
    opened_ind: date = DateValidator(required=True)
    folder: pathlib.Path = PathValidator(required=True, path_exists=True)
    host: str = IPv4Validator(required=True)

    @host.pre_validate
    def not_already_filed(self, value: str) -> str:
        folder = getattr(self, "folder", None)
        if folder is not None and self.archive.already_filed(folder, value):
            raise ValueError(f"already filed {folder} from {value}")
        return value

    @host.post_set
    def commit_filing(self, value: str) -> None:
        self.archive.commit(self.folder, value)


class FilingService:
    """Composition root. Production: ``FilingService(S3Archive(bucket))``."""

    def __init__(self, archive: Archive) -> None:
        self.archive = archive

    def file(
        self,
        opened_eu: str | date,
        opened_ind: str | date,
        folder: str | pathlib.Path,
        host: str,
    ) -> FiledDocument:
        return FiledDocument(
            archive=self.archive,
            opened_eu=opened_eu,
            opened_ind=opened_ind,
            folder=folder,
            host=host,
        )


def main() -> FiledDocument:
    service = FilingService(InMemoryArchive())
    row = service.file(
        opened_eu="2020-01-02",
        opened_ind="02/01/2020",
        folder=".",
        host="127.0.0.1",
    )
    try:
        service.file("2020-01-02", "02/01/2020", ".", "127.0.0.1")
    except ValueError:
        pass
    try:
        FilingService(InMemoryArchive()).file(
            "2020-13-40", "02/01/2020", ".", "127.0.0.1"
        )
    except ValueError:
        pass
    try:
        FilingService(InMemoryArchive()).file(
            datetime(2020, 1, 2), "02/01/2020", ".", "127.0.0.1"
        )
    except TypeError:
        pass
    return row


if __name__ == "__main__":
    filed = main()
    print(f"opened {filed.opened_eu.isoformat()} at {filed.folder} ({filed.host})")
