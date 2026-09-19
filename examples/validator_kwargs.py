# SPDX-License-Identifier: MIT
"""Every Validator constructor kwarg, live-checked.

This is the constructor map in ``docs/reference/validator.md``, not a
product workflow. Copy a snippet; leave logger OFF in production.
"""

import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from ux_valio import (
    IntegerValidator,
    StringValidator,
    UUIDValidator,
    ValidationErrors,
    Validator,
)


def _must_raise(fn, *types: type[BaseException]) -> None:
    try:
        fn()
    except types:
        return
    raise AssertionError(f"expected {types}")


@dataclass
class Profile:
    bio: str = StringValidator(
        max_length=160,
        required=True,
        min_length=1,
        doc="Public bio, 160 chars.",
    )
    rank: str = Validator(
        in_choice=["Male", "Female", "Trans"],
        default="Female",
    )
    seats: int = IntegerValidator(
        min_value=0, max_value=10, multiple_of=2, default=2
    )
    account_id: UUID = UUIDValidator(default_factory=uuid4)
    token: str = StringValidator(reassign=False, default="init")
    pin: str = StringValidator(length=4, default="0000")


def main() -> Profile:
    desc = Profile.__dict__["bio"]
    if desc.doc != "Public bio, 160 chars.":
        raise AssertionError(desc.doc)
    if desc.__doc__ != desc.doc:
        raise AssertionError(desc.__doc__)
    if desc.name != "bio":
        raise AssertionError(desc.name)
    if Profile.__dict__["rank"].logger is not False:
        raise AssertionError("logger omitted stays OFF")

    row = Profile(bio="Ada")
    if row.rank != "Female":
        raise AssertionError(row.rank)
    if row.seats != 2:
        raise AssertionError(row.seats)
    if row.pin != "0000":
        raise AssertionError(row.pin)
    if not isinstance(row.account_id, UUID):
        raise AssertionError(row.account_id)

    other = Profile(bio="Bob")
    if other.account_id == row.account_id:
        raise AssertionError("default_factory must mint a new UUID")

    zero = Profile(bio="Ada", seats=0)
    if zero.seats != 0:
        raise AssertionError("falsy 0 must not be replaced by default")

    _must_raise(lambda: Profile(bio=None), ValueError)  # required
    _must_raise(lambda: Profile(bio=""), ValueError)  # min_length
    _must_raise(lambda: Profile(bio="Ada", seats=3), ValueError)
    _must_raise(
        lambda: Profile(bio="Ada", seats=-3), ValueError, ValidationErrors
    )
    _must_raise(lambda: Profile(bio="Ada", pin="12"), ValueError)
    _must_raise(lambda: setattr(row, "token", "other"), AttributeError)

    del row.token
    row.token = "other"

    _must_raise(
        lambda: StringValidator(default="", default_factory=str),
        TypeError,
    )
    _must_raise(
        lambda: IntegerValidator(min_value=0, gt=0),
        ValueError,
    )
    _must_raise(
        lambda: IntegerValidator(value=1, eq=2),
        ValueError,
    )

    @dataclass
    class Pair:
        n: int = IntegerValidator(eq=2, debug=True)

    assert Pair(n=2).n == 2
    _must_raise(lambda: Pair(n=3), ValueError)

    log = logging.getLogger("examples.validator_kwargs.scratch")
    tagged = StringValidator(doc="x", logger=log, debug=True)

    @dataclass
    class Tagged:
        s: str = tagged

    assert Tagged.__dict__["s"].doc == "x"
    assert Tagged.__dict__["s"].logger is log

    print(
        f"bio={row.bio!r} rank={row.rank} seats={zero.seats} "
        f"pin={row.pin} token={row.token} doc={desc.doc!r}"
    )
    return row


if __name__ == "__main__":
    main()
