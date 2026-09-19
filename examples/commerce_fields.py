# SPDX-License-Identifier: MIT
"""Publish a storefront: host + slug uniqueness, catalog identities.

Facades prove host/slug/GTIN/ZIP. Uniqueness hangs on ``post_validate``.
``catalog`` is the injected store, not a column.
"""

from dataclasses import dataclass
from typing import Protocol

from ux_valio import (
    CurrencyCodeValidator,
    GTINValidator,
    HostnameValidator,
    SlugValidator,
    TimezoneValidator,
    ULIDValidator,
    USZipCodeValidator,
)


class StoreCatalog(Protocol):
    """Host uniqueness. Production: unique index on tenant host."""

    def host_taken(self, host: str) -> bool:
        """True when this hostname is already published."""
        ...

    def commit(self, host: str) -> None:
        """Persist after a successful set."""
        ...


class InMemoryStoreCatalog:
    """Runnable fake. Plug in DNS/tenant table that satisfies ``StoreCatalog``."""

    def __init__(self, hosts: set[str] | None = None) -> None:
        self._hosts = {host.casefold() for host in (hosts or set())}

    def host_taken(self, host: str) -> bool:
        return host.casefold() in self._hosts

    def commit(self, host: str) -> None:
        self._hosts.add(host.casefold())


@dataclass(init=False)
class Storefront:
    public_id: str = ULIDValidator(required=True)
    host: str = HostnameValidator(required=True)
    slug: str = SlugValidator(required=True)
    gtin: str = GTINValidator()
    currency: str = CurrencyCodeValidator(required=True)
    tz: str = TimezoneValidator(required=True)
    zip: str = USZipCodeValidator()

    def __init__(
        self,
        public_id: str,
        host: str,
        slug: str,
        currency: str,
        tz: str,
        *,
        catalog: StoreCatalog,
        gtin: str | None = None,
        zip: str | None = None,
    ) -> None:
        self.catalog = catalog
        self.public_id = public_id
        self.host = host
        self.slug = slug
        self.gtin = gtin
        self.currency = currency
        self.tz = tz
        self.zip = zip

    @host.post_validate
    def host_available(self, value: str) -> str:
        if self.catalog.host_taken(value):
            raise ValueError(f"host {value!r} is already published")
        return value

    @tz.post_set
    def commit_host(self, value: str) -> None:
        self.catalog.commit(self.host)


class StorefrontService:
    """Composition root. Production: ``StorefrontService(SqlStoreCatalog(pool))``."""

    def __init__(self, catalog: StoreCatalog) -> None:
        self.catalog = catalog

    def publish(
        self,
        public_id: str,
        host: str,
        slug: str,
        currency: str,
        tz: str,
        *,
        gtin: str | None = None,
        zip: str | None = None,
    ) -> Storefront:
        return Storefront(
            public_id,
            host,
            slug,
            currency,
            tz,
            catalog=self.catalog,
            gtin=gtin,
            zip=zip,
        )


def main() -> Storefront:
    taken = StorefrontService(InMemoryStoreCatalog(hosts={"shop.example.com"}))
    row = StorefrontService(InMemoryStoreCatalog()).publish(
        public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        host="API.Example.COM.",
        slug="Hello-World",
        currency="inr",
        tz="Asia/Kolkata",
        gtin="036000291452",
        zip="90210-1234",
    )
    try:
        taken.publish(
            public_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            host="shop.example.com",
            slug="taken",
            currency="USD",
            tz="UTC",
        )
    except ValueError:
        pass
    return row


if __name__ == "__main__":
    created = main()
    print(created.host, created.slug, created.currency)
