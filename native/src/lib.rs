//! Optional apply peer for `ux-valio[native]`.
//!
//! Closed plan for `IntegerValidator(min_value=…)`: `Integer` then
//! `MinValue(i64)`. Host compiles once at bind; each set is one FFI
//! `apply(plan, i64)`. Failures are `FailKind` — host formats KEEP wording.
//! Soul stays on the host (descriptor, hooks, store). Not Cap Door B.

use pyo3::prelude::*;

/// Specified scalar units. `Integer` is the `i64` extract at the FFI
/// boundary; the match arm is the plan shape, not a second type check.
#[derive(Clone, Copy)]
enum Unit {
    Integer,
    MinValue(i64),
}

/// Compiled plan. Built once; applied many times.
#[pyclass(frozen)]
struct Plan {
    units: [Unit; 2],
}

/// Small error kind. Host formats messages; this crate does not.
/// Type misses never leave the host (`isinstance` gates before apply).
#[pyclass(eq, eq_int, skip_from_py_object)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum FailKind {
    /// Value was less than the compiled `MinValue` bound.
    MinValue = 1,
}

fn apply_units(units: [Unit; 2], value: i64) -> Result<(), FailKind> {
    for unit in units {
        match unit {
            Unit::Integer => {}
            Unit::MinValue(min) if value < min => return Err(FailKind::MinValue),
            Unit::MinValue(_) => {}
        }
    }
    Ok(())
}

/// Product peer: `compile(min_value)` + `apply(plan, i64) -> Option[FailKind]`.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. `Integer` is the `i64`
/// argument extract.
#[pymodule]
mod ux_valio_native {
    use super::*;

    #[pymodule_export]
    use super::FailKind;

    #[pymodule_export]
    use super::Plan;

    /// Closed plan: `Integer` + `MinValue(min_value)`. Same specified
    /// theory as unconstrained `IntegerValidator(min_value=…)`.
    #[pyfunction]
    fn compile(min_value: i64) -> Plan {
        Plan {
            units: [Unit::Integer, Unit::MinValue(min_value)],
        }
    }

    /// One-shot apply. Success is `None`; bound miss is `FailKind.MinValue`.
    ///
    /// `i64` extract is the range oracle: a Python int outside i64 raises
    /// `OverflowError` at this FFI boundary (host falls through). Releases
    /// the GIL for the plan body (`Python::detach`). The plan is an owned
    /// copy of two `Copy` units; the scalar is `i64`.
    #[pyfunction]
    fn apply(py: Python<'_>, plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        let units = plan.units;
        py.detach(|| apply_units(units, value).err())
    }
}
