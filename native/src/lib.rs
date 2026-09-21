//! Optional apply peer for `ux-valio[native]`.
//!
//! Closed Integer bound plans: `Integer` then the specified i64 units
//! (`MinValue` / `MaxValue` / `GreaterThan` / `LessThan` / `Equal`,
//! including min+max range and exclusive pairs). Host compiles once at
//! bind; each set is one FFI `apply(plan, i64)`. Failures are
//! `FailKind` — host formats KEEP wording. Soul stays on the host
//! (descriptor, hooks, store). Not Cap Door B.

use pyo3::prelude::*;

/// Specified scalar units. `Integer` is the plan-shape marker; type
/// extract is host `isinstance` plus the FFI `i64` argument.
#[derive(Clone, Copy)]
enum Unit {
    /// Plan-shape marker. Type extract is host `isinstance` + FFI i64.
    Integer,
    /// Host `min_value`, inclusive ≥.
    MinValue(i64),
    /// Host `max_value`, inclusive ≤.
    MaxValue(i64),
    /// Host `gt`, exclusive >.
    GreaterThan(i64),
    /// Host `lt`, exclusive <.
    LessThan(i64),
    /// Host `eq`/`value`, exact.
    Equal(i64),
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
}

fn apply_units(units: &[Unit], value: i64) -> Result<(), FailKind> {
    for unit in units {
        match *unit {
            Unit::Integer => {}
            Unit::MinValue(bound) if value < bound => return Err(FailKind::MinValue),
            Unit::MinValue(_) => {}
            Unit::MaxValue(bound) if value > bound => return Err(FailKind::MaxValue),
            Unit::MaxValue(_) => {}
            Unit::GreaterThan(bound) if value <= bound => return Err(FailKind::GreaterThan),
            Unit::GreaterThan(_) => {}
            Unit::LessThan(bound) if value >= bound => return Err(FailKind::LessThan),
            Unit::LessThan(_) => {}
            Unit::Equal(bound) if value != bound => return Err(FailKind::Equal),
            Unit::Equal(_) => {}
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
/// `None` is `Ok(())`. A `FailKind` is `Err`. `Integer` is the plan
/// shape; `i64` extract is the FFI argument. Compile kwargs are host
/// names (`min_value` / `gt` / `max_value` / `lt` / `eq`) mapped onto
/// the full-word units. Not a taught L1 API.
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
    /// is `compile(min_value=0, max_value=10)`. Host `gt`/`lt`/`eq`
    /// map to `GreaterThan` / `LessThan` / `Equal`.
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
        push_bound(&mut units, gt, Unit::GreaterThan);
        push_bound(&mut units, max_value, Unit::MaxValue);
        push_bound(&mut units, lt, Unit::LessThan);
        push_bound(&mut units, eq, Unit::Equal);
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
