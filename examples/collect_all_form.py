# SPDX-License-Identifier: MIT
"""Signup form: ``collect_all=True`` continues remaining concerns on a field.

Default Door A is fail-fast. ``collect_all=True`` with ``debug=True`` surfaces
``ValidationErrors`` for every concern on that descriptor (min, max, multiple
of, named facade extra). It is per-field, not per-dataclass: the first field
that fails still stops later fields. Callers catch ``ValidationErrors`` and
map ``err.errors`` to form messages.
"""

from dataclasses import dataclass

from ux_valio import (
    EmailValidator,
    IntegerValidator,
    StringValidator,
    ValidationErrors,
)


@dataclass
class SignupForm:
    username: str = StringValidator(
        debug=True,
        required=True,
        min_length=3,
        max_length=32,
        collect_all=True,
    )
    email: str = EmailValidator(debug=True, required=True, collect_all=True)
    seats: int = IntegerValidator(
        min_value=0,
        max_value=10,
        multiple_of=2,
        collect_all=True,
        debug=True,
        required=True,
    )


def submit_signup(username: str, email: str, seats: int) -> SignupForm:
    """Submit the form. Multi-concern failures raise ``ValidationErrors``."""
    return SignupForm(username=username, email=email, seats=seats)


def form_messages(err: ValidationErrors) -> list[str]:
    """Map collected failures to caller-facing strings."""
    return [str(item) for item in err.errors]


def main() -> SignupForm:
    ok = submit_signup(username="ada", email="ada@example.com", seats=8)
    try:
        submit_signup(username="ada", email="ada@example.com", seats=7)
    except ValidationErrors as err:
        form_messages(err)
    try:
        submit_signup(username="ada", email="ada@example.com", seats=-3)
    except ValidationErrors as err:
        form_messages(err)
    return ok


if __name__ == "__main__":
    submitted = main()
    print(f"{submitted.username} seats={submitted.seats}")
