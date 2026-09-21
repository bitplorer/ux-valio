//! Measure-only apply stub. Not a product door.
//!
//! Closed plan for `IntegerValidator(min_value=0)`: `IntDoor` then `Ge(0)`.
//! `compile` once; `apply(plan, i64)` is one FFI call. Failures are
//! `FailKind` (host would format KEEP wording). Do not ship as
//! `ux-valio[native]`.

use pyo3::prelude::*;

/// Specified scalar units. `IntDoor` is the `i64` extract at the FFI
/// boundary; the match arm is the plan shape, not a second type check.
#[derive(Clone, Copy)]
enum Unit {
    IntDoor,
    Ge(i64),
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
    /// Value was not an integer (`IntDoor`). Unreachable when `apply`
    /// takes `i64` — CPython/PyO3 reject the extract first.
    NotInt = 1,
    /// Value was less than the compiled `Ge` bound.
    Ge = 2,
}

fn apply_plan(plan: &Plan, value: i64) -> Result<(), FailKind> {
    for unit in plan.units {
        match unit {
            Unit::IntDoor => {}
            Unit::Ge(min) if value < min => return Err(FailKind::Ge),
            Unit::Ge(_) => {}
        }
    }
    Ok(())
}

/// Bench stub: `compile` + `apply(plan, i64) -> Result<(), FailKind>`.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. `IntDoor` is the `i64`
/// argument extract.
#[pymodule]
mod ux_valio_peer_bench {
    use super::*;

    #[pymodule_export]
    use super::FailKind;

    #[pymodule_export]
    use super::Plan;

    /// Closed plan: `IntDoor` + `Ge(0)`. Same specified theory as
    /// unconstrained `IntegerValidator(min_value=0)`.
    #[pyfunction]
    fn compile() -> Plan {
        Plan {
            units: [Unit::IntDoor, Unit::Ge(0)],
        }
    }

    /// One-shot apply. Success is `None`; `Ge` is `FailKind.Ge`.
    #[pyfunction]
    fn apply(plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        apply_plan(&plan, value).err()
    }
}
