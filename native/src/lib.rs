//! Optional apply peer for `ux-valio[native]`.
//!
//! Closed Integer bound plans: `Integer` then the specified i64 units
//! (`MinValue` / `MaxValue` / `Gt` / `Lt` / `Eq`, including min+max
//! range and exclusive pairs). Host compiles once at bind; each set is
//! one FFI `apply(plan, i64)`. Failures are `FailKind` — host formats
//! KEEP wording. Soul stays on the host (descriptor, hooks, store).
//! Not Cap Door B.

use pyo3::prelude::*;

/// Specified scalar units. `Integer` is the `i64` extract at the FFI
/// boundary; the match arm is the plan shape, not a second type check.
#[derive(Clone, Copy)]
enum Unit {
    Integer,
    MinValue(i64),
    MaxValue(i64),
    Gt(i64),
    Lt(i64),
    Eq(i64),
}

/// Compiled plan. Built once; applied many times.
///
/// Owned `Vec` so a single-bound plan and a min+max range share one
/// type — not a fixed two-slot array.
#[pyclass(frozen)]
struct Plan {
    units: Vec<Unit>,
}

/// Small error kind. Host formats messages; this crate does not.
/// Type misses never leave the host (`isinstance` gates before apply).
#[pyclass(eq, eq_int, skip_from_py_object)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum FailKind {
    /// Value was less than the compiled `MinValue` bound.
    MinValue = 1,
    /// Value was greater than the compiled `MaxValue` bound.
    MaxValue = 2,
    /// Value was not strictly greater than the compiled `Gt` bound.
    Gt = 3,
    /// Value was not strictly less than the compiled `Lt` bound.
    Lt = 4,
    /// Value was not the compiled `Eq` value.
    Eq = 5,
}

fn apply_units(units: &[Unit], value: i64) -> Result<(), FailKind> {
    for unit in units {
        match *unit {
            Unit::Integer => {}
            Unit::MinValue(min) if value < min => return Err(FailKind::MinValue),
            Unit::MinValue(_) => {}
            Unit::MaxValue(max) if value > max => return Err(FailKind::MaxValue),
            Unit::MaxValue(_) => {}
            Unit::Gt(gt) if value <= gt => return Err(FailKind::Gt),
            Unit::Gt(_) => {}
            Unit::Lt(lt) if value >= lt => return Err(FailKind::Lt),
            Unit::Lt(_) => {}
            Unit::Eq(eq) if value != eq => return Err(FailKind::Eq),
            Unit::Eq(_) => {}
        }
    }
    Ok(())
}

fn push_bound(units: &mut Vec<Unit>, bound: Option<i64>, unit: impl FnOnce(i64) -> Unit) {
    if let Some(value) = bound {
        units.push(unit(value));
    }
}

/// Product peer: `compile(...)` + `apply(plan, i64) -> Option[FailKind]`.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. `Integer` is the `i64`
/// argument extract. Bound kwargs match host `ValueValidator` order
/// (min family, max family, eq). Not a taught L1 API.
#[pymodule]
mod ux_valio_native {
    use super::*;

    #[pymodule_export]
    use super::FailKind;

    #[pymodule_export]
    use super::Plan;

    /// Closed Integer bound plan. Omitted kwargs stay off the unit list.
    ///
    /// `compile(5)` is still `MinValue(5)` (positional first arg). Range
    /// is `compile(min_value=0, max_value=10)`.
    #[pyfunction]
    #[pyo3(signature = (min_value=None, max_value=None, gt=None, lt=None, eq=None))]
    fn compile(
        min_value: Option<i64>,
        max_value: Option<i64>,
        gt: Option<i64>,
        lt: Option<i64>,
        eq: Option<i64>,
    ) -> Plan {
        let mut units = Vec::with_capacity(4);
        units.push(Unit::Integer);
        // Host `_validate_value` order: min_value / gt, then max_value / lt, then eq.
        push_bound(&mut units, min_value, Unit::MinValue);
        push_bound(&mut units, gt, Unit::Gt);
        push_bound(&mut units, max_value, Unit::MaxValue);
        push_bound(&mut units, lt, Unit::Lt);
        push_bound(&mut units, eq, Unit::Eq);
        Plan { units }
    }

    /// One-shot apply. Success is `None`; bound miss is a `FailKind`.
    ///
    /// `i64` extract is the range oracle: a Python int outside i64 raises
    /// `OverflowError` at this FFI boundary (host falls through). Releases
    /// the GIL for the plan body (`Python::detach`). The plan is an owned
    /// clone of `Copy` units; the scalar is `i64`.
    #[pyfunction]
    fn apply(py: Python<'_>, plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        let units = plan.units.clone();
        py.detach(move || apply_units(&units, value).err())
    }
}
