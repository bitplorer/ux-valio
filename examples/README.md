# Examples

Copy-pasteable production skeletons: `field: T = SomeValidator(...)`.
Import names from `ux_valio`. There is no Field twin, Schema twin, Cap Host,
or list/dict/set/tuple collection facade.

Each file is a service-shaped module callers copy: a Protocol port, an
in-memory fake, a validated dataclass, and a service that injects ports
before product ``__init__`` (ports are not dataclass fields). The service
constructor holds the ports. Hooks (`pre_validate` / `validator` / `post_set`) fail closed into
`ValueError` / `ValidationErrors`. Omitted `debug` / `collect_all` are True.
`main()` is
only the runnable runner (wire the fake, show the conflict path). Replace
the fake with a SQL/Redis/HTTP adapter that satisfies the Protocol. Examples
do not ship a DB driver.

Password hashing stays in the example `PasswordHasher` port (`Pbkdf2PasswordHasher`
uses stdlib PBKDF2 with a **fixed demo salt**). Production replaces that fake
with bcrypt or argon2id and a unique salt per row. The store keeps only the
hash — never plaintext. Do not add a hasher to `ux_valio`.

| Scenario | File | Port to replace | Fake | Production plug |
| --- | --- | --- | --- | --- |
| Signup + login (password strength, confirm, hash-on-create, `collect_all`) | `collect_all_form.py` | `UserStore`, `PasswordHasher` | `InMemoryUserStore`, `Pbkdf2PasswordHasher` | SQL unique index; bcrypt/argon2id (unique per-row salt) |
| Minimal account (username uniqueness, email, UUID) | `user_account.py` | `AccountDirectory` | `InMemoryAccountDirectory` | unique index on username |
| Username reservation (`pre_validate` + `post_set` persist) | `registration.py` | `UserStore`, `PasswordHasher` | `InMemoryUserStore`, `Pbkdf2PasswordHasher` | same unique index + hasher as signup |
| Paid checkout (card ∩ Luhn, card `MM/YY`, promo window) | `checkout.py` | `PromoCatalog`, `Inventory`, `PaymentGateway` | `InMemoryPromoCatalog`, `InMemoryInventory`, `StubPaymentGateway` | offers table, stock row or Redis, Stripe/Razorpay (decline → `ValueError`) |
| India KYC (Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, `region="IN"`) | `indian_kyc.py` | `IdentityRegistry` | `InMemoryIdentityRegistry` | KYC warehouse unique Aadhaar/PAN |
| Named identities (GSTIN uniqueness, IBAN, BIC) | `identity_fields.py` | `VendorRegistry` | `InMemoryVendorRegistry` | unique GSTIN in the vendor store |
| TypedDict invite (`Annotated` + name policy + email uniqueness) | `typed_dict_schema.py` | `InviteLog` | `InMemoryInviteLog` | unique invite email |
| Staff profile (`&` / `\|`, `AllOf` / `AnyOf`, compose-root `pre_validate`) | `compose_hooks.py` | `StaffDirectory` | `InMemoryStaffDirectory` | HRIS/LDAP unique display name |
| Publish storefront (host uniqueness, slug, GTIN, ZIP) | `commerce_fields.py` | `StoreCatalog` | `InMemoryStoreCatalog` | unique tenant host |
| Filed document (EU/IND dates, `path_exists`, archive uniqueness) | `dates_paths.py` | `Archive` | `InMemoryArchive` | unique (folder, host) |
| Catalog SKU (`Pattern` algebra + SKU uniqueness) | `sku_codes.py` | `PartCatalog` | `InMemoryPartCatalog` | unique index on SKU |
| Warehouse line (lookarounds + stock reserve) | `lookaround_units.py` | `Warehouse` | `InMemoryWarehouse` | stock row |

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
python examples/identity_fields.py
python examples/commerce_fields.py
python examples/typed_dict_schema.py
```

`indian_kyc.py` uses optional extra `phonenumbers` for the IN phone door
(`pip install ux-valio[phonenumbers]`). Identity ∩ registry still run when
the extra is missing. Production installs the extra and keeps
`PhoneNumberValidator(region="IN")`.
