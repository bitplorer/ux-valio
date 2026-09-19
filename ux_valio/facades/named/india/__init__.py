# SPDX-License-Identifier: MIT
"""India statutory identity. Folder of domain layers.

Sibling layers (do not import each other)::

    kyc       — person documents (Aadhaar, PAN, Voter)
    gst       — GST invoice (GSTIN, HSN)
    registry  — TAN, CIN, Udyam
    bank      — IFSC, PIN, UPI

Parallel to ``named.finance`` / ``named.catalog``. Public names
still re-export from ``ux_valio``; navigation is
``from ux_valio.facades.named.india.gst import GSTINValidator``.
"""

from ux_valio.facades.named.india.bank import (
    IFSCValidator,
    PinCodeValidator,
    UPIIdValidator,
)
from ux_valio.facades.named.india.gst import GSTINValidator, HSNCodeValidator
from ux_valio.facades.named.india.kyc import (
    AadhaarCardValidator,
    PANCardValidator,
    VoterIdValidator,
)
from ux_valio.facades.named.india.registry import (
    CINValidator,
    TANValidator,
    UdyamValidator,
)

__all__ = [
    "AadhaarCardValidator",
    "CINValidator",
    "GSTINValidator",
    "HSNCodeValidator",
    "IFSCValidator",
    "PANCardValidator",
    "PinCodeValidator",
    "TANValidator",
    "UPIIdValidator",
    "UdyamValidator",
    "VoterIdValidator",
]
