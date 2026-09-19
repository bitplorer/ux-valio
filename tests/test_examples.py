# SPDX-License-Identifier: MIT
"""Examples stay importable example scripts (no Field / Schema / Cap)."""

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from ux_valio import ValidationErrors

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = ROOT / "examples"
EXAMPLE_MODULES = (
    "user_account",
    "registration",
    "checkout",
    "indian_kyc",
    "dates_paths",
    "sku_codes",
    "lookaround_units",
    "compose_hooks",
    "collect_all_form",
    "typed_dict_schema",
    "identity_fields",
    "commerce_fields",
)


def test_examples_readme_lists_files():
    text = (EXAMPLE_DIR / "README.md").read_text()
    assert "Field twin" in text
    assert "python examples/" in text
    for name in EXAMPLE_MODULES:
        assert f"{name}.py" in text


def test_examples_readme_is_a_port_index():
    """Scenario → file → Protocol → fake → production plug."""
    text = (EXAMPLE_DIR / "README.md").read_text()
    assert "UserStore" in text
    assert "PromoCatalog" in text
    assert "Inventory" in text
    assert "PaymentGateway" in text
    assert "IdentityRegistry" in text
    assert "StaffDirectory" in text
    assert "InMemoryUserStore" in text
    assert "do not ship a DB driver" in text
    assert "constructor" in text
    assert "PasswordHasher" in text
    assert "bcrypt" in text
    assert "argon2" in text
    for needle in (
        "unique index",
        "Stripe",
        "Redis",
        "KYC",
    ):
        assert needle in text


@pytest.mark.parametrize("modname", EXAMPLE_MODULES)
def test_example_main_runs(modname):
    import importlib

    module = importlib.import_module(f"examples.{modname}")
    assert callable(module.main)
    module.main()


@pytest.mark.parametrize("modname", EXAMPLE_MODULES)
def test_example_files_do_not_import_pytest(modname):
    path = EXAMPLE_DIR / f"{modname}.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "pytest" or alias.name.startswith("pytest."):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "pytest" or node.module.startswith("pytest."):
                hits.append(node.module)
    assert hits == []


def test_examples_are_not_a_second_product_door():
    import ux_valio

    assert "examples" not in ux_valio.__all__
    assert not hasattr(ux_valio, "Field")
    assert not hasattr(ux_valio, "Schema")
    assert not hasattr(ux_valio, "PasswordHasher")
    assert not hasattr(ux_valio, "Pbkdf2PasswordHasher")


def test_service_examples_inject_ports_in_the_constructor():
    """Ports are constructor deps, not process-global bind_* holders."""
    for name in (
        "collect_all_form",
        "registration",
        "checkout",
        "indian_kyc",
        "compose_hooks",
        "user_account",
        "identity_fields",
        "commerce_fields",
        "sku_codes",
        "lookaround_units",
        "dates_paths",
        "typed_dict_schema",
    ):
        src = (EXAMPLE_DIR / f"{name}.py").read_text()
        assert "bind_" not in src
        assert "global USERS" not in src
        assert "global PROMOS" not in src
        assert "global INVENTORY" not in src
        assert "global GATEWAY" not in src
        assert "global REGISTRY" not in src
        assert "global DIRECTORY" not in src


DEMO_PASSWORD = "Secret1a"


def test_registration_port_is_validated():
    from examples.registration import Registration

    with pytest.raises(TypeError, match="UserStore"):
        Registration(
            users="not-a-store",
            hasher=object(),
            username="ada",
            password="Secret1a",
            password_confirm="Secret1a",
        )


def test_signup_username_conflict_is_a_validation_failure():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
    )

    service = SignupService(InMemoryUserStore(taken={"ada"}), Pbkdf2PasswordHasher())
    with pytest.raises((ValueError, ValidationErrors), match="already"):
        service.submit(
            username="ada",
            email="ada@example.com",
            password=DEMO_PASSWORD,
            password_confirm=DEMO_PASSWORD,
            seats=8,
        )


def test_signup_short_name_collects_length_without_the_store():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
        form_messages,
    )

    service = SignupService(InMemoryUserStore(), Pbkdf2PasswordHasher())
    with pytest.raises(ValueError) as err:
        service.submit(
            username="ab",
            email="ada@example.com",
            password=DEMO_PASSWORD,
            password_confirm=DEMO_PASSWORD,
            seats=8,
        )
    assert form_messages(err.value)


def test_signup_collect_all_surfaces_multiple_seat_concerns():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
        form_messages,
    )

    service = SignupService(InMemoryUserStore(), Pbkdf2PasswordHasher())
    with pytest.raises(ValidationErrors) as err:
        service.submit(
            username="ada",
            email="ada@example.com",
            password=DEMO_PASSWORD,
            password_confirm=DEMO_PASSWORD,
            seats=-3,
        )
    messages = form_messages(err.value)
    assert len(messages) >= 2


def test_signup_stores_hashed_password_not_plaintext():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
    )

    users = InMemoryUserStore()
    hasher = Pbkdf2PasswordHasher()
    SignupService(users, hasher).submit(
        username="ada",
        email="ada@example.com",
        password=DEMO_PASSWORD,
        password_confirm=DEMO_PASSWORD,
        seats=8,
    )
    stored = users.get("ada")
    assert stored is not None
    assert stored.password_hash != DEMO_PASSWORD
    assert DEMO_PASSWORD not in stored.password_hash
    assert hasher.verify(DEMO_PASSWORD, stored.password_hash)
    assert stored.email == "ada@example.com"


def test_signup_password_confirm_mismatch_is_a_validation_failure():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
    )

    users = InMemoryUserStore()
    with pytest.raises(ValueError, match="match"):
        SignupService(users, Pbkdf2PasswordHasher()).submit(
            username="ada",
            email="ada@example.com",
            password=DEMO_PASSWORD,
            password_confirm="Secret1b",
            seats=8,
        )
    assert not users.username_taken("ada")


def test_signup_weak_password_is_a_validation_failure():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
    )

    service = SignupService(InMemoryUserStore(), Pbkdf2PasswordHasher())
    with pytest.raises((ValueError, ValidationErrors)):
        service.submit(
            username="ada",
            email="ada@example.com",
            password="short",
            password_confirm="short",
            seats=8,
        )
    with pytest.raises((ValueError, ValidationErrors)):
        service.submit(
            username="ada",
            email="ada@example.com",
            password="nodigitshere",
            password_confirm="nodigitshere",
            seats=8,
        )


def test_signup_login_verify_failure_is_a_clear_error():
    from examples.collect_all_form import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        SignupService,
    )

    users = InMemoryUserStore()
    hasher = Pbkdf2PasswordHasher()
    service = SignupService(users, hasher)
    service.submit(
        username="ada",
        email="ada@example.com",
        password=DEMO_PASSWORD,
        password_confirm=DEMO_PASSWORD,
        seats=8,
    )
    logged_in = service.login(username="ada", password=DEMO_PASSWORD)
    assert logged_in.username == "ada"
    with pytest.raises(ValueError, match="invalid"):
        service.login(username="ada", password="Wrong1a")
    with pytest.raises(ValueError, match="invalid"):
        service.login(username="missing", password=DEMO_PASSWORD)


def test_registration_conflict_does_not_consume_the_name():
    from examples.registration import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        RegistrationService,
    )

    store = InMemoryUserStore(taken={"taken"})
    service = RegistrationService(store, Pbkdf2PasswordHasher())
    with pytest.raises(ValueError, match="already"):
        service.register("taken", DEMO_PASSWORD, DEMO_PASSWORD)
    assert store.username_taken("taken")
    assert not store.username_taken("fresh")
    row = service.register("fresh", DEMO_PASSWORD, DEMO_PASSWORD)
    assert row.username == "fresh"
    assert store.username_taken("fresh")
    stored = store.get("fresh")
    assert stored is not None
    assert stored.password_hash != DEMO_PASSWORD


def test_registration_invalid_name_does_not_commit():
    from examples.registration import (
        InMemoryUserStore,
        Pbkdf2PasswordHasher,
        RegistrationService,
    )

    store = InMemoryUserStore()
    with pytest.raises(ValueError):
        RegistrationService(store, Pbkdf2PasswordHasher()).register(
            "ab", DEMO_PASSWORD, DEMO_PASSWORD
        )
    assert not store.username_taken("ab")


def test_checkout_unknown_promo_is_a_validation_failure():
    from examples.checkout import (
        CheckoutService,
        InMemoryInventory,
        InMemoryPromoCatalog,
        StubPaymentGateway,
    )

    service = CheckoutService(
        promos=InMemoryPromoCatalog(codes={"SPRING30"}),
        inventory=InMemoryInventory(stock={"WIDGET": 10}),
        gateway=StubPaymentGateway(),
    )
    with pytest.raises(ValueError, match="promo"):
        service.place(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="NOPE",
            sku="WIDGET",
            quantity=1,
        )


def test_checkout_stock_and_gateway_failures_are_validation_errors():
    from examples.checkout import (
        CheckoutService,
        InMemoryInventory,
        InMemoryPromoCatalog,
        StubPaymentGateway,
    )

    promos = InMemoryPromoCatalog(codes={"SPRING30"})
    with pytest.raises(ValueError, match="stock|inventory|available"):
        CheckoutService(
            promos=promos,
            inventory=InMemoryInventory(stock={"WIDGET": 1}),
            gateway=StubPaymentGateway(),
        ).place(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
            sku="WIDGET",
            quantity=99,
        )
    with pytest.raises(ValueError, match="declin"):
        CheckoutService(
            promos=promos,
            inventory=InMemoryInventory(stock={"WIDGET": 10}),
            gateway=StubPaymentGateway(declines={"4111111111111111"}),
        ).place(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
            sku="WIDGET",
            quantity=1,
        )


def test_kyc_already_registered_identity_is_a_validation_failure():
    from examples.indian_kyc import (
        VALID_AADHAAR,
        VALID_PAN,
        InMemoryIdentityRegistry,
        KycService,
    )

    with pytest.raises((ValueError, ValidationErrors), match="aadhaar|already"):
        KycService(
            InMemoryIdentityRegistry(aadhaars={VALID_AADHAAR}, pans=set())
        ).submit(VALID_AADHAAR, VALID_PAN, phone=None)
    with pytest.raises((ValueError, ValidationErrors), match="PAN|pan|already"):
        KycService(
            InMemoryIdentityRegistry(aadhaars=set(), pans={VALID_PAN})
        ).submit(VALID_AADHAAR, VALID_PAN, phone=None)


def test_indian_kyc_imports_without_phonenumbers(monkeypatch):
    import builtins
    import importlib
    import sys

    real_import = builtins.__import__

    def blocked(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "phonenumbers" or name.startswith("phonenumbers."):
            raise ImportError("blocked for example smoke")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked)
    sys.modules.pop("examples.indian_kyc", None)
    module = importlib.import_module("examples.indian_kyc")
    assert callable(module.main)
    assert module.HAS_PHONENUMBERS is False
    module.main()
    sys.modules.pop("examples.indian_kyc", None)


def test_staff_directory_conflict_hangs_on_compose_root():
    from examples.compose_hooks import InMemoryStaffDirectory, StaffService

    directory = InMemoryStaffDirectory(taken={"Ada"})
    service = StaffService(directory)
    with pytest.raises(ValueError, match="already|taken|directory"):
        service.create(name="  Ada  ", tag="ops", note=7, title="Engineer")
    row = service.create(name="  Grace  ", tag="ops", note=7, title="Engineer")
    assert row.name == "Grace"
    assert directory.name_taken("Grace")


def test_account_username_conflict_does_not_commit():
    from examples.user_account import AccountService, InMemoryAccountDirectory

    directory = InMemoryAccountDirectory(taken={"ada"})
    with pytest.raises(ValueError, match="already"):
        AccountService(directory).open(username="Ada", email="ada@example.com")
    assert not directory.username_taken("grace")
    row = AccountService(InMemoryAccountDirectory()).open(
        username="  Grace  ", email="grace@example.com"
    )
    assert row.username == "grace"


def test_vendor_gstin_conflict_is_a_validation_failure():
    from examples.identity_fields import InMemoryVendorRegistry, VendorService

    taken = VendorService(InMemoryVendorRegistry(gstins={"09AAAPA1111F1ZP"}))
    with pytest.raises(ValueError, match="already|GSTIN"):
        taken.onboard(
            gstin="09AAAPA1111F1ZP",
            iban="GB82 WEST 1234 5698 7654 32",
            bic="DEUTDEFF",
        )
