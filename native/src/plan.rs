//! Typed plan. Each variant owns only that family's checks.
//!
//! [`PyPlan`] is the frozen object Python calls `Plan`. It holds one
//! [`Plan`] variant — Integer bounds, Float bounds, String length, Bytes
//! length, an IntegerEnum member set, a StringEnum member set, or a
//! Boolean / Decimal type-door marker. There is no shared unit bag.

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
    /// Host `min_value`: value was less than the inclusive bound.
    MinValue = 1,
    /// Host `max_value`: value was greater than the inclusive bound.
    MaxValue = 2,
    /// Host `gt`: value was not strictly greater than the bound.
    GreaterThan = 3,
    /// Host `lt`: value was not strictly less than the bound.
    LessThan = 4,
    /// Host `eq`/`value`: value was not the compiled equal.
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
}

/// Frozen peer object. Python name is `Plan`. The body is one [`Plan`]
/// variant. Apply clones the `Arc` inside that variant.
#[pyclass(frozen, name = "Plan")]
pub(crate) struct PyPlan {
    pub(crate) body: Plan,
}

pub(crate) fn share_plan(body: Plan) -> PyPlan {
    PyPlan { body }
}

/// Host never applies a plan through another family's door. A direct
/// call that does is a peer `RuntimeError` (fail closed).
pub(crate) fn unexpected_family(door: &str) -> PyErr {
    PyRuntimeError::new_err(format!("{door} plan family mismatch"))
}

pub(crate) fn apply_member_units(members: &[i64], value: i64) -> Result<(), FailKind> {
    if members.iter().any(|member| *member == value) {
        Ok(())
    } else {
        Err(FailKind::NotMember)
    }
}

pub(crate) fn apply_string_members(members: &[String], value: &str) -> Result<(), FailKind> {
    if members.iter().any(|member| member == value) {
        Ok(())
    } else {
        Err(FailKind::NotMember)
    }
}
