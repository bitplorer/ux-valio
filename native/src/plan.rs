//! Typed plan. Each variant owns only that family's checks.
//!
//! [`PyPlan`] is the frozen object Python calls `Plan`. It holds one
//! [`Plan`] variant — Integer bounds, Float bounds, String length, Bytes
//! length, an IntegerEnum member set, a StringEnum member set, or a
//! Boolean / Decimal / Date / DateTime / Uuid / Path type-door marker,
//! or an IP string-identity kind. There is no shared unit bag.

use std::sync::Arc;

use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

use crate::bound::BoundUnit;
use crate::length::LengthUnit;

/// Small error kind. Host formats KEEP messages via the FailKind map.
/// Type misses never leave the host (`isinstance` before apply — Python
/// `True` is `int`; Python `int` is not `float`). Bound units run after
/// the scalar extract.
#[pyclass(eq, eq_int, skip_from_py_object)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum FailKind {
    /// Host `min_value`. Pass when `value >= bound`; miss when `value < bound`.
    MinValue = 1,
    /// Host `max_value`. Pass when `value <= bound`; miss when `value > bound`.
    MaxValue = 2,
    /// Host `gt` (exclusive). Pass when `value > bound`; miss when `value <= bound`.
    GreaterThan = 3,
    /// Host `lt` (exclusive). Pass when `value < bound`; miss when `value >= bound`.
    LessThan = 4,
    /// Host `eq`/`value`. Pass when `value == bound`; miss when `value != bound`.
    /// IEEE NaN never equals.
    Equal = 5,
    /// Host `min_length`: count was less than the inclusive bound.
    /// String: codepoints. Bytes: `len(bytes)`.
    MinLength = 6,
    /// Host `max_length`: count was greater than the inclusive bound.
    /// String: codepoints. Bytes: `len(bytes)`.
    MaxLength = 7,
    /// Host exact `length`: count was not the compiled length.
    /// String: codepoints. Bytes: `len(bytes)`.
    Length = 8,
    /// Host IntegerEnum / StringEnum type door: extracted scalar was not
    /// a compiled member value. Host formats the KEEP type-door
    /// `TypeError`.
    NotMember = 9,
    /// Host IP string identity: the extracted `str` is not an address
    /// of the compiled kind (`ipv4` / `ipv6` / `ip`). Host formats the
    /// KEEP `ValueError`.
    NotIp = 10,
}

/// One compiled family. The variant's payload is the only check list
/// that family can run. Apply clones the inner `Arc`, not this enum.
pub(crate) enum Plan {
    /// `i64` extract, then [`BoundUnit<i64>`](BoundUnit).
    Integer(Arc<Vec<BoundUnit<i64>>>),
    /// `f64` extract, then [`BoundUnit<f64>`](BoundUnit).
    Float(Arc<Vec<BoundUnit<f64>>>),
    /// `&str` extract, then [`LengthUnit`] (Unicode scalar count).
    String(Arc<Vec<LengthUnit>>),
    /// `&[u8]` extract, then [`LengthUnit`] (byte count).
    Bytes(Arc<Vec<LengthUnit>>),
    /// `i64` extract, then exact membership in this set.
    IntegerEnum(Arc<Vec<i64>>),
    /// `&str` extract, then exact UTF-8 membership in this set.
    StringEnum(Arc<Vec<String>>),
    /// Exact `bool` extract. No bound unit.
    Boolean,
    /// Exact `decimal.Decimal` extract. No bound unit. No scale unit.
    Decimal,
    /// Exact `datetime.date` extract. `datetime.datetime` is a `date`
    /// subclass and extracts here. No bound unit. String coerce stays
    /// on the host.
    Date,
    /// Exact `datetime.datetime` extract. A plain `datetime.date` does
    /// not extract. No bound unit. String coerce stays on the host.
    DateTime,
    /// Exact `uuid.UUID` extract. A raw `str` does not extract. No
    /// bound unit. String coerce stays on the host.
    Uuid,
    /// `str` extract, then IPv4 / IPv6 / either identity. The stored
    /// value stays that string. No bound unit.
    Ip(IpKind),
    /// Exact `pathlib.Path` extract. A raw `str` does not extract.
    /// `pathlib.PurePath` is not a `Path`. No bound unit. No
    /// filesystem check. String coerce stays on the host.
    Path,
}

/// Which stdlib parser the IP plan mirrors.
///
/// `V4` is `ipaddress.IPv4Address`, `V6` is `ipaddress.IPv6Address`,
/// `Either` is `ipaddress.ip_address` (v4, then v6).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum IpKind {
    V4,
    V6,
    Either,
}

/// Frozen native plan object. Python name is `Plan`. The body is one [`Plan`]
/// variant. Apply clones the `Arc` inside that variant.
#[pyclass(frozen, name = "Plan")]
pub(crate) struct PyPlan {
    pub(crate) body: Plan,
}

pub(crate) fn share_plan(body: Plan) -> PyPlan {
    PyPlan { body }
}

/// Host never applies a plan through another family's door. A direct
/// call that does is a native-module `RuntimeError` (fail closed).
pub(crate) fn unexpected_family(door: &str) -> PyErr {
    PyRuntimeError::new_err(format!("{door} plan family mismatch"))
}

pub(crate) fn apply_i64_members(members: &[i64], value: i64) -> Result<(), FailKind> {
    if members.iter().any(|member| *member == value) {
        Ok(())
    } else {
        Err(FailKind::NotMember)
    }
}

pub(crate) fn apply_str_members(members: &[String], value: &str) -> Result<(), FailKind> {
    if members.iter().any(|member| member == value) {
        Ok(())
    } else {
        Err(FailKind::NotMember)
    }
}
