# SPDX-License-Identifier: MIT
"""Field-level logging: one logger per descriptor.

``logger=True`` binds ``logging.getLogger("module.Class.field")`` at
``__set_name__``. Get/set/delete are INFO; failures are ERROR. The
stored value is not in the message (no Aadhaar in logs). Omitted
``logger`` / ``logger=False`` / ``logger=None`` are OFF. ux-valio never
opens a file — pass your own ``logging.Logger`` if you want a
FileHandler.

This is not a product workflow. Copy it when you need to *see* one
field. Production forms leave logger OFF. Docs: ``docs/how-to/logging.md``.
"""

import logging
import sys
from dataclasses import dataclass

from ux_valio import IntegerValidator, StringValidator, ValidationErrors

# App-owned logger: you add handlers. The library does not.
audit = logging.getLogger("boxoffice.audit")
audit.setLevel(logging.INFO)
if not audit.handlers:
    sink = logging.StreamHandler(sys.stderr)
    sink.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
    audit.addHandler(sink)
    audit.propagate = False


def _must_raise(fn, *types: type[BaseException]) -> None:
    try:
        fn()
    except types:
        return
    raise AssertionError(f"expected {types}")


@dataclass
class Ticket:
    """``holder`` and ``seats`` log; ``note`` does not."""

    holder: str = StringValidator(required=True, min_length=2, logger=True)
    seats: int = IntegerValidator(
        min_value=0, max_value=10, multiple_of=2, logger=True
    )
    note: str = StringValidator(default="", logger=False)


@dataclass
class Refund:
    """Stable name ``boxoffice.audit`` instead of ``module.Refund.reason``."""

    reason: str = StringValidator(required=True, min_length=3, logger=audit)


def main() -> Ticket:
    holder_log = Ticket.__dict__["holder"].logger
    seats_log = Ticket.__dict__["seats"].logger
    note_log = Ticket.__dict__["note"].logger
    if not isinstance(holder_log, logging.Logger):
        raise AssertionError("logger=True should bind a stdlib Logger")
    if not holder_log.name.endswith(".Ticket.holder"):
        raise AssertionError(holder_log.name)
    if not seats_log.name.endswith(".Ticket.seats"):
        raise AssertionError(seats_log.name)
    if note_log is not False:
        raise AssertionError("omitted/False logger stays OFF")
    if Refund.__dict__["reason"].logger is not audit:
        raise AssertionError("custom Logger must be kept")

    ok = Ticket(holder="Ada", seats=4, note="window")
    _ = ok.holder  # INFO get on holder only
    refund = Refund(reason="duplicate charge")

    _must_raise(lambda: Ticket(holder="Ada", seats=9), ValueError)
    _must_raise(
        lambda: Ticket(holder="Ada", seats=-3), ValueError, ValidationErrors
    )
    _must_raise(lambda: Refund(reason="no"), ValueError)

    print(
        f"{ok.holder} seats={ok.seats} note={ok.note!r} "
        f"holder_log={holder_log.name} refund={refund.reason}"
    )
    return ok


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    main()
