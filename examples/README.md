# Examples

One file per real-world workflow. Copy the file; replace the in-memory
port with SQL/Redis/HTTP. `field: T = SomeValidator(...)`. There is no
Field twin, Schema twin, Cap Host, or list/dict/set/tuple collection
facade.

Each file is a service-shaped module: a `@runtime_checkable` Protocol
port, an in-memory fake, a validated dataclass, and a service that
injects ports in the constructor. Ports are
`Validator[Port](required=True)` with `field(repr=False, compare=False)`.
Hooks (`pre_validate` / `post_validate` / `post_set`) fail closed into
`ValueError` / `ValidationErrors`. Omitted `debug` / `collect_all` are
True. `main()` runs the happy path **and** `_must_raise` on conflict /
identity failures so `python examples/<file>.py` is a live check, not a
silent `except: pass`. Examples do not ship a DB driver.

Password hashing stays in the example `PasswordHasher` port
(`Pbkdf2PasswordHasher` uses stdlib PBKDF2 with a **fixed demo salt**).
Production replaces that fake with bcrypt or argon2id and a unique salt
per row. The store keeps only the hash — never plaintext. Do not add a
hasher to `ux_valio`.

| Workflow | File | Ports | Fake | Production |
| --- | --- | --- | --- | --- |
| Registration + login | `signup.py` | `UserStore`, `PasswordHasher` | `InMemoryUserStore`, `Pbkdf2PasswordHasher` | SQL unique index; bcrypt/argon2id |
| Paid checkout | `checkout.py` | `PromoCatalog`, `Inventory`, `PaymentGateway` | `InMemoryPromoCatalog`, `InMemoryInventory`, `StubPaymentGateway` | offers table, stock/Redis, Stripe/Razorpay |
| India KYC | `kyc.py` | `IdentityRegistry` | `InMemoryIdentityRegistry` | unique Aadhaar/PAN |
| Vendor onboarding | `vendor.py` | `VendorRegistry` | `InMemoryVendorRegistry` | unique GSTIN |
| Publish storefront | `storefront.py` | `StoreCatalog` | `InMemoryStoreCatalog` | unique tenant host |
| Catalog line (SKU + units + stock) | `catalog.py` | `PartCatalog`, `Warehouse` | `InMemoryPartCatalog`, `InMemoryWarehouse` | unique SKU + stock row |
| Invite (TypedDict schema) | `invite.py` | `InviteLog` | `InMemoryInviteLog` | unique invite email |
| File a document | `filing.py` | `Archive` | `InMemoryArchive` | unique (folder, host) |
| Field-level logging | `field_logging.py` | — | stdlib `logging` | your `Logger` / `FileHandler` |

```console
python examples/signup.py
python examples/checkout.py
python examples/kyc.py
python examples/vendor.py
python examples/storefront.py
python examples/catalog.py
python examples/invite.py
python examples/filing.py
python examples/field_logging.py
```

`kyc.py` uses optional extra `phonenumbers` for the IN phone door
(`pip install ux-valio[phonenumbers]`). Identity ∩ registry still run when
the extra is missing. Production installs the extra and keeps
`PhoneNumberValidator(region="IN")`.
