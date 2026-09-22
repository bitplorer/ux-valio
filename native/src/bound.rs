//! Bound checks owned by the Integer and Float plan variants.
//!
//! One compare (`scalar_miss`) and one builder (`compile_bound_plan`)
//! serve both families. The walk sees `BoundUnit<T>` only, so a length
//! unit or a Decimal marker cannot be passed in.

use std::sync::Arc;

use crate::plan::FailKind;

/// Inclusive and exclusive scalar checks. `T` is the door (`i64` or `f64`).
#[derive(Clone, Copy)]
pub(crate) enum BoundUnit<T> {
    /// Host `min_value`, inclusive ≥.
    MinValue(T),
    /// Host `max_value`, inclusive ≤.
    MaxValue(T),
    /// Host `gt`, exclusive >.
    GreaterThan(T),
    /// Host `lt`, exclusive <.
    LessThan(T),
    /// Host `eq`/`value`, exact. IEEE `!=` so NaN never equals NaN.
    Equal(T),
}

/// Door A IEEE compares. `PartialOrd`/`PartialEq` match host Python:
/// NaN unordered (min/max/gt/lt pass), `nan != nan` (`eq` fails).
/// Do not use `total_cmp` — that would be a second policy. One compare
/// for `i64` and `f64`; the scalar type is the door.
#[allow(clippy::float_cmp)]
pub(crate) fn scalar_miss<T: PartialOrd>(kind: FailKind, value: T, bound: T) -> Option<FailKind> {
    let missed = match kind {
        FailKind::MinValue => value < bound,
        FailKind::MaxValue => value > bound,
        FailKind::GreaterThan => value <= bound,
        FailKind::LessThan => value >= bound,
        FailKind::Equal => value != bound,
        FailKind::MinLength | FailKind::MaxLength | FailKind::Length | FailKind::NotMember => {
            unreachable!("scalar_miss compares bound units")
        }
    };
    missed.then_some(kind)
}

fn push_bound<T>(units: &mut Vec<BoundUnit<T>>, bound: Option<T>, unit: fn(T) -> BoundUnit<T>) {
    if let Some(value) = bound {
        units.push(unit(value));
    }
}

/// Specified bound units in host `_validate_value` order. The `Arc` is
/// what apply clones; the units are not copied per set.
pub(crate) fn compile_bound_plan<T: Copy>(
    min_value: Option<T>,
    max_value: Option<T>,
    gt: Option<T>,
    lt: Option<T>,
    eq: Option<T>,
) -> Arc<Vec<BoundUnit<T>>> {
    let mut units = Vec::with_capacity(5);
    push_bound(&mut units, min_value, BoundUnit::MinValue);
    push_bound(&mut units, gt, BoundUnit::GreaterThan);
    push_bound(&mut units, max_value, BoundUnit::MaxValue);
    push_bound(&mut units, lt, BoundUnit::LessThan);
    push_bound(&mut units, eq, BoundUnit::Equal);
    Arc::new(units)
}

/// Walk bound units only. A new `BoundUnit` variant fails to compile
/// here. Length and member checks are a different type.
pub(crate) fn apply_bound_units<T: Copy + PartialOrd>(
    units: &[BoundUnit<T>],
    value: T,
) -> Result<(), FailKind> {
    for unit in units {
        let fail = match *unit {
            BoundUnit::MinValue(bound) => scalar_miss(FailKind::MinValue, value, bound),
            BoundUnit::MaxValue(bound) => scalar_miss(FailKind::MaxValue, value, bound),
            BoundUnit::GreaterThan(bound) => scalar_miss(FailKind::GreaterThan, value, bound),
            BoundUnit::LessThan(bound) => scalar_miss(FailKind::LessThan, value, bound),
            BoundUnit::Equal(bound) => scalar_miss(FailKind::Equal, value, bound),
        };
        if let Some(kind) = fail {
            return Err(kind);
        }
    }
    Ok(())
}
