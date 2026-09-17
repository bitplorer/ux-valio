# Door A examples

Copy-pasteable production skeletons: `field: T = SomeValidator(...)`.
Import names from `ux_valio`. There is no Field twin, Schema twin, Cap Host,
or list/dict/set/tuple collection facade.

Each file is a service-shaped module callers copy: a Protocol port, an
in-memory fake, a Door A dataclass, and hooks that fail closed into
`ValueError` / `ValidationErrors`. `debug=True` is fail-closed. `main()`
wires the fake and shows the conflict path. Replace the fake with a
SQL/Redis/HTTP adapter that satisfies the Protocol. Examples do not ship a DB driver.

Hooks (`add_pre_validator` / `add_validator` / `add_post_set`) plus
injectable ports are the production pattern — the way a service would
wire a uniqueness check, payment gateway stub, or KYC store.

| Scenario | File | Port to replace | Fake | Production plug |
| --- | --- | --- | --- | --- |
| Signup form (`collect_all=True` → `ValidationErrors`) | `collect_all_form.py` | `UserStore` | `InMemoryUserStore` | SQL unique index / `SELECT` username |
| Username reservation (`add_pre_validator` + `add_post_set`) | `registration.py` | `UserStore` | `InMemoryUserStore` | same unique index; commit after store |
| Paid checkout (card ∩ Luhn, card `MM/YY` Pattern, promo window) | `checkout.py` | `PromoCatalog`, `Inventory`, `PaymentGateway` | `InMemoryPromoCatalog`, `InMemoryInventory`, `StubPaymentGateway` | offers table, stock row or Redis, Stripe/Razorpay (decline → `ValueError`) |
| India KYC (Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, `region="IN"`) | `indian_kyc.py` | `IdentityRegistry` | `InMemoryIdentityRegistry` | KYC warehouse unique Aadhaar/PAN |
| Staff profile (`&` / `\|`, `AllOf` / `AnyOf`, compose-root `add_*`) | `compose_hooks.py` | `StaffDirectory` | `InMemoryStaffDirectory` | HRIS/LDAP unique display name |
| Open a user account (string, int, email, UUID, choice) | `user_account.py` | — | — | copy the dataclass; uniqueness lives on `UserStore` in the signup files |
| Filed document (EU/IND `DateValidator`, `PathValidator`, IPv4) | `dates_paths.py` | — | — | copy the dataclass; `path_exists=True` is the filesystem door |
| Catalog SKU (`Pattern`, `StartsWith`, `EndsWith`, `SetOf`, stdlib atoms) | `sku_codes.py` | — | — | copy the Pattern algebra; names KEEP |
| Warehouse units (`IfPrecededBy` / `IfFollowedBy` on Door A fields) | `lookaround_units.py` | — | — | copy the lookaround units |

```console
python examples/user_account.py
python examples/registration.py
python examples/checkout.py
python examples/indian_kyc.py
python examples/dates_paths.py
python examples/sku_codes.py
python examples/lookaround_units.py
python examples/compose_hooks.py
python examples/collect_all_form.py
```

`indian_kyc.py` uses optional extra `phonenumbers` for the IN phone door
(`pip install ux-valio[phonenumbers]`). Identity ∩ registry still run when
the extra is missing. Production installs the extra and keeps
`PhoneNumberValidator(region="IN")`.
