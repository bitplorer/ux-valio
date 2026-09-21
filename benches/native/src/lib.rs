//! Measure-only apply stub. Not a published extra.
//!
//! Closed plan for `IntegerValidator(min_value=0)`: `Integer` then
//! `MinValue(0)`. `compile` once; `apply(plan, i64)` is one FFI call.
//! Failures are `FailKind` (host would format KEEP wording). Do not ship
//! as `ux-valio[native]`.

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

/// Small error kind. Host formats messages; this stub does not.
#[pyclass(eq, eq_int, skip_from_py_object)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum FailKind {
    /// Value was not an integer. Unreachable when `apply` takes `i64` —
    /// CPython/PyO3 reject the extract first.
    NotInteger = 1,
    /// Value was less than the compiled `MinValue` bound.
    MinValue = 2,
}

fn apply_plan(plan: &Plan, value: i64) -> Result<(), FailKind> {
    for unit in plan.units {
        match unit {
            Unit::Integer => {}
            Unit::MinValue(min) if value < min => return Err(FailKind::MinValue),
            Unit::MinValue(_) => {}
        }
    }
    Ok(())
}

/// Bench stub: `compile` + `apply(plan, i64) -> Result<(), FailKind>`.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. `Integer` is the `i64`
/// argument extract.
#[pymodule]
mod ux_valio_peer_bench {
    use super::*;

    #[pymodule_export]
    use super::FailKind;

    #[pymodule_export]
    use super::Plan;

    /// Closed plan: `Integer` + `MinValue(0)`. Same specified theory as
    /// unconstrained `IntegerValidator(min_value=0)`.
    #[pyfunction]
    fn compile() -> Plan {
        Plan {
            units: [Unit::Integer, Unit::MinValue(0)],
        }
    }

    /// One-shot apply. Success is `None`; bound miss is `FailKind.MinValue`.
    #[pyfunction]
    fn apply(plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        apply_plan(&plan, value).err()
    }
}
