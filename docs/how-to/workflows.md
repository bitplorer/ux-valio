# Workflows (copy-paste)

A workflow is a **form + ports + service**. The form is a dataclass.
The ports are Protocol adapters (SQL, Redis, Stripe) injected in
declaration order. The service is the composition root your HTTP handler
calls. You copy **one file** from [`examples/`](../../examples/) and
replace the in-memory fake.

`python examples/<file>.py` runs the happy path and `_must_raise` on
the conflict/identity failures. If a failure path is silently `except:
pass`, a regression would print OK. Examples do not ship a DB driver.

**When to copy which file**

| workflow | file | you replace |
|---|---|---|
| Registration + login | `signup.py` | `UserStore`, `PasswordHasher` |
| Paid checkout | `checkout.py` | promo, stock, gateway |
| India KYC | `kyc.py` | Aadhaar/PAN registry |
| Vendor onboarding | `vendor.py` | GSTIN registry |
| Storefront | `storefront.py` | tenant host catalog |
| Catalog line | `catalog.py` | SKU index + stock |
| Invite (TypedDict) | `invite.py` | invite email log |
| File a document | `filing.py` | archive uniqueness |

## Shared skeleton

```python
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from ux_valio import StringValidator, Validator

@runtime_checkable
class UserStore(Protocol):
    def username_taken(self, username: str) -> bool: ...
    def commit(self, username: str) -> None: ...

@dataclass
class Register:
    users: UserStore = field(
        default=Validator[UserStore](required=True),
        repr=False,
        compare=False,
    )
    username: str = StringValidator(required=True, min_length=3)

    @username.pre_validate
    def fold(self, value: str) -> str:
        return value.strip().casefold()

    @username.post_validate
    def username_not_taken(self, value: str) -> str:
        if self.users.username_taken(value):
            raise ValueError("username already registered")
        return value

    @username.post_set
    def commit(self, value: str) -> None:
        self.users.commit(value)
```

Declaration order is the init order: the port is assigned **before**
`username`, so uniqueness can see `self.users`. `repr=False, compare=False`
keeps the store out of `repr` / `eq`. `InitVar` is too late — see
[choices](../explanation/choices.md).

Password hashing stays in an example `PasswordHasher` port (stdlib
PBKDF2, **fixed demo salt**). Production: bcrypt/argon2id, unique salt
per row. Do not add a hasher to `ux_valio`.

`PhoneNumberValidator` needs `pip install ux-valio[phonenumbers]` and
`region="IN"`. Identity ∩ registry in `kyc.py` still run without the extra.
