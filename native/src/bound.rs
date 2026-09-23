//! Bound checks owned by the Integer and Float plan variants.
//!
//! One compare (`scalar_miss`) and one builder (`compile_bound_plan`)
//! serve both families. The walk sees `BoundUnit<T>` only, so a length
//! unit or a Decimal marker cannot be passed in.

use std::sync::Arc;

use crate::plan::FailKind;

/// Scalar checks. `T` is the door (`i64` or `f64`).
///
/// Each variant's compare in [`scalar_miss`] is a **fail-when** predicate
/// (the arm is true when the value misses). Inclusive bounds are
/// `min_value` / `max_value`. Exclusive bounds are `gt` / `lt`.
#[derive(Clone, Copy)]
pub(crate) enum BoundUnit<T> {
    /// Host `min_value`. Pass when `value >= bound`; miss when `value < bound`.
    MinValue(T),
    /// Host `max_value`. Pass when `value <= bound`; miss when `value > bound`.
    MaxValue(T),
    /// Host `gt` (exclusive). Pass when `value > bound`; miss when `value <= bound`.
    GreaterThan(T),
    /// Host `lt` (exclusive). Pass when `value < bound`; miss when `value >= bound`.
    LessThan(T),
    /// Host `eq`/`value`. Pass when `value == bound`; miss when `value != bound`.
    /// IEEE: NaN never equals.
    Equal(T),
}

/// Door A IEEE compares. `PartialOrd`/`PartialEq` match host Python:
/// NaN unordered (min/max/gt/lt pass), `nan != nan` (`eq` fails).
/// Do not use `total_cmp` — that would be a second policy. One compare
/// for `i64` and `f64`; the scalar type is the door.
///
/// Each arm is the **miss** (fail-when):
/// `min_value` passes `value >= bound`; `gt` passes `value > bound`
/// (exclusive, so equal misses); `max_value` passes `value <= bound`;
/// `lt` passes `value < bound` (exclusive, so equal misses); `eq` passes
/// only exact equality.
#[allow(clippy::float_cmp)]
pub(crate) fn scalar_miss<T: PartialOrd>(kind: FailKind, value: T, bound: T) -> Option<FailKind> {
    let missed = match kind {
        // pass when value >= bound; miss when value < bound
        FailKind::MinValue => value < bound,
        // pass when value <= bound; miss when value > bound
        FailKind::MaxValue => value > bound,
        // pass when value > bound; miss when value <= bound (exclusive)
        FailKind::GreaterThan => value <= bound,
        // pass when value < bound; miss when value >= bound (exclusive)
        FailKind::LessThan => value >= bound,
        // pass when value == bound; miss when value != bound (NaN never equals)
        FailKind::Equal => value != bound,
        FailKind::MinLength
        | FailKind::MaxLength
        | FailKind::Length
        | FailKind::NotMember
        | FailKind::NotIp => {
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
