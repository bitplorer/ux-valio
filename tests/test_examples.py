# SPDX-License-Identifier: MIT
"""Examples stay importable Door A scripts (no Field / Schema / Cap)."""

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
    assert not hasattr(ux_valio, "ListValidator")


def test_signup_username_conflict_is_a_validation_failure():
    from examples.collect_all_form import InMemoryUserStore, submit_signup

    users = InMemoryUserStore(taken={"ada"})
    with pytest.raises((ValueError, ValidationErrors), match="already"):
        submit_signup(
            username="ada",
            email="ada@example.com",
            seats=8,
            users=users,
        )


def test_signup_collect_all_joins_length_and_uniqueness():
    from examples.collect_all_form import InMemoryUserStore, form_messages, submit_signup

    users = InMemoryUserStore(taken={"ab"})
    with pytest.raises(ValidationErrors) as err:
        submit_signup(
            username="ab",
            email="ada@example.com",
            seats=8,
            users=users,
        )
    messages = " ".join(form_messages(err.value))
    assert "already" in messages
    assert "ab" in messages


def test_signup_collect_all_surfaces_multiple_seat_concerns():
    from examples.collect_all_form import InMemoryUserStore, form_messages, submit_signup

    users = InMemoryUserStore()
    with pytest.raises(ValidationErrors) as err:
        submit_signup(
            username="ada",
            email="ada@example.com",
            seats=-3,
            users=users,
        )
    messages = form_messages(err.value)
    assert len(messages) >= 2


def test_registration_conflict_does_not_consume_the_name():
    from examples.registration import InMemoryUserStore, register_username

    store = InMemoryUserStore(taken={"taken"})
    with pytest.raises(ValueError, match="already"):
        register_username("taken", users=store)
    assert store.username_taken("taken")
    assert not store.username_taken("fresh")
    row = register_username("fresh", users=store)
    assert row.username == "fresh"
    assert store.username_taken("fresh")


def test_registration_invalid_name_does_not_commit():
    from examples.registration import InMemoryUserStore, register_username

    store = InMemoryUserStore()
    with pytest.raises(ValueError):
        register_username("ab", users=store)
    assert not store.username_taken("ab")


def test_checkout_unknown_promo_is_a_validation_failure():
    from examples.checkout import (
        InMemoryInventory,
        InMemoryPromoCatalog,
        StubPaymentGateway,
        place_order,
    )

    with pytest.raises(ValueError, match="promo"):
        place_order(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="NOPE",
            sku="WIDGET",
            quantity=1,
            promos=InMemoryPromoCatalog(codes={"SPRING30"}),
            inventory=InMemoryInventory(stock={"WIDGET": 10}),
            gateway=StubPaymentGateway(),
        )


def test_checkout_stock_and_gateway_failures_are_validation_errors():
    from examples.checkout import (
        InMemoryInventory,
        InMemoryPromoCatalog,
        StubPaymentGateway,
        place_order,
    )

    promos = InMemoryPromoCatalog(codes={"SPRING30"})
    with pytest.raises(ValueError, match="stock|inventory|available"):
        place_order(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
            sku="WIDGET",
            quantity=99,
            promos=promos,
            inventory=InMemoryInventory(stock={"WIDGET": 1}),
            gateway=StubPaymentGateway(),
        )
    with pytest.raises(ValueError, match="declin"):
        place_order(
            holder="Ada Lovelace",
            number="4111111111111111",
            card_expiry="12/28",
            amount=Decimal("19.99"),
            promo_code="SPRING30",
            sku="WIDGET",
            quantity=1,
            promos=promos,
            inventory=InMemoryInventory(stock={"WIDGET": 10}),
            gateway=StubPaymentGateway(declines={"4111111111111111"}),
        )


def test_kyc_already_registered_identity_is_a_validation_failure():
    from examples.indian_kyc import (
        VALID_AADHAAR,
        VALID_PAN,
        InMemoryIdentityRegistry,
        submit_kyc,
    )

    registry = InMemoryIdentityRegistry(aadhaars={VALID_AADHAAR}, pans=set())
    with pytest.raises((ValueError, ValidationErrors), match="aadhaar|already"):
        submit_kyc(
            VALID_AADHAAR,
            VALID_PAN,
            registry=registry,
            phone=None,
        )
    registry = InMemoryIdentityRegistry(aadhaars=set(), pans={VALID_PAN})
    with pytest.raises((ValueError, ValidationErrors), match="PAN|pan|already"):
        submit_kyc(
            VALID_AADHAAR,
            VALID_PAN,
            registry=registry,
            phone=None,
        )


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
    from examples.compose_hooks import InMemoryStaffDirectory, create_profile

    directory = InMemoryStaffDirectory(taken={"Ada"})
    with pytest.raises(ValueError, match="already|taken|directory"):
        create_profile(
            name="  Ada  ",
            tag="ops",
            note=7,
            title="Engineer",
            directory=directory,
        )
    row = create_profile(
        name="  Grace  ",
        tag="ops",
        note=7,
        title="Engineer",
        directory=directory,
    )
    assert row.name == "Grace"
    assert directory.name_taken("Grace")
