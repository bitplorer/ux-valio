# Door A examples

Copy-pasteable dataclasses that use the taught door: `field: T = SomeValidator(...)`.
Import names from `ux_valio`. There is no Field twin, Schema twin, Cap Host,
or list/dict/set/tuple collection facade.

Each file is a production scenario: a domain model, a constructor callers would
call, and fail-closed handling (`debug=True` raises; `collect_all=True` on forms
surfaces `ValidationErrors`). Run any file with `python examples/<file>.py`.

| Scenario | File |
| --- | --- |
| Open a user account (string, int, email, UUID, choice) | `user_account.py` |
| Reserve a unique username (`add_pre_validator` + `add_post_set`) | `registration.py` |
| Paid checkout (payment card ∩ Luhn, card `MM/YY` Pattern, amount, promo `ExpiryValidator`) | `checkout.py` |
| India KYC (Aadhaar ∩ Verhoeff, PAN ∩ Luhn mod 26, `PhoneNumberValidator(region="IN")`) | `indian_kyc.py` |
| Filed document (EU/IND `DateValidator`, `PathValidator`, IPv4) | `dates_paths.py` |
| Catalog SKU (`Pattern`, `StartsWith`, `EndsWith`, `SetOf`, stdlib atoms) | `sku_codes.py` |
| Warehouse units (`IfPrecededBy` / `IfFollowedBy` on Door A fields) | `lookaround_units.py` |
| Staff profile (`&` / `\|`, `AllOf` / `AnyOf`, compose-root `add_*`) | `compose_hooks.py` |
| Signup form (`collect_all=True` → `ValidationErrors`) | `collect_all_form.py` |

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

`indian_kyc.py` needs the optional extra: `pip install ux-valio[phonenumbers]`.
