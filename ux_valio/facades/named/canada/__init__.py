# SPDX-License-Identifier: MIT
"""Canada statutory identity. Folder of domain layers.

Sibling layers (do not import each other)::

    postal — postal code
    kyc    — SIN

Parallel to ``named.us`` / ``named.uk``. Public names re-export
from ``ux_valio``.
"""

from ux_valio.facades.named.canada.kyc import CanadianSINValidator
from ux_valio.facades.named.canada.postal import CAPostalCodeValidator

__all__ = [
    "CAPostalCodeValidator",
    "CanadianSINValidator",
]
