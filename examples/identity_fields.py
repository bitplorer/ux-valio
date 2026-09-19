# SPDX-License-Identifier: MIT
"""Vendor onboarding: GSTIN + IBAN identities, registry uniqueness.

Facades prove the identity string (compact store, no portal). Uniqueness
hangs on ``post_validate`` (after checksum). Persist on ``post_set``.
``registry`` is wired by ``VendorService`` before ``__init__``, not a field.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    BICValidator,
    CINValidator,
    GSTINValidator,
    IBANValidator,
    ISBNValidator,
    MACAddressValidator,
)


class VendorRegistry(Protocol):
    """Already-onboarded GSTIN. Production: unique GSTIN in the vendor store."""

    def gstin_taken(self, gstin: str) -> bool:
        """True when this GSTIN is already on file."""
        ...

    def commit(self, gstin: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryVendorRegistry:
    """Runnable fake. Plug in the vendor warehouse that satisfies ``VendorRegistry``."""

    def __init__(self, gstins: set[str] | None = None) -> None:
        self._gstins = set(gstins or ())

    def gstin_taken(self, gstin: str) -> bool:
        return gstin in self._gstins

    def commit(self, gstin: str) -> None:
        self._gstins.add(gstin)


def _bind(cls, ports, **fields):
    """Wire service ports onto a new instance, then product ``__init__``."""
    inst = object.__new__(cls)
    for name, port in ports.items():
        object.__setattr__(inst, name, port)
    cls.__init__(inst, **fields)
    return inst


@dataclass
class Vendor:
    gstin: str = GSTINValidator(required=True)
    iban: str = IBANValidator(required=True)
    bic: str = BICValidator(required=True)
    cin: str = CINValidator()
    isbn: str = ISBNValidator()
    mac: str = MACAddressValidator()

    @gstin.post_validate
    def gstin_available(self, value: str) -> str:
        if self.registry.gstin_taken(value):
            raise ValueError(f"GSTIN {value!r} is already onboarded")
        return value

    @bic.post_set
    def commit_gstin(self, value: str) -> None:
        self.registry.commit(self.gstin)


class VendorService:
    """Composition root. Production: ``VendorService(SqlVendorRegistry(pool))``."""

    def __init__(self, registry: VendorRegistry) -> None:
        self.registry = registry

    def onboard(
        self,
        gstin: str,
        iban: str,
        bic: str,
        *,
        cin: str | None = None,
        isbn: str | None = None,
        mac: str | None = None,
    ) -> Vendor:
        return _bind(
            Vendor,
            {"registry": self.registry},
            gstin=gstin,
            iban=iban,
            bic=bic,
            cin=cin,
            isbn=isbn,
            mac=mac,
        )


def main() -> Vendor:
    taken = VendorService(
        InMemoryVendorRegistry(gstins={"09AAAPA1111F1ZP"})
    )
    row = VendorService(InMemoryVendorRegistry()).onboard(
        gstin="09 AAAPA1111F 1Z P",
        iban="GB82 WEST 1234 5698 7654 32",
        bic="deutdeff",
        cin="u12345mh2000ptc123456",
        isbn="978-0-306-40615-7",
        mac="aa:bb:cc:dd:ee:ff",
    )
    try:
        taken.onboard(
            gstin="09AAAPA1111F1ZP",
            iban="GB82 WEST 1234 5698 7654 32",
            bic="DEUTDEFF",
        )
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    created = main()
    print(created.gstin, created.iban, created.bic)
