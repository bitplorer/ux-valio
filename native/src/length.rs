//! Length checks owned by the String and Bytes plan variants.
//!
//! The FFI door counts (Unicode scalars or bytes) and passes that count
//! in. This walk sees `LengthUnit` only, so a bound unit cannot be passed
//! in. String and Bytes share the walk; the count is the door.

use std::sync::Arc;

use crate::plan::FailKind;

/// Host length kwargs. The count's meaning is chosen at the FFI door.
#[derive(Clone, Copy)]
pub(crate) enum LengthUnit {
    /// Host `min_length`, inclusive.
    MinLength(usize),
    /// Host `max_length`, inclusive.
    MaxLength(usize),
    /// Host exact `length`.
    Length(usize),
}

fn push_length(units: &mut Vec<LengthUnit>, bound: Option<usize>, unit: fn(usize) -> LengthUnit) {
    if let Some(value) = bound {
        units.push(unit(value));
    }
}

/// Specified length units in host `_validate_length` order.
pub(crate) fn compile_length_plan(
    min_length: Option<usize>,
    max_length: Option<usize>,
    length: Option<usize>,
) -> Arc<Vec<LengthUnit>> {
    let mut units = Vec::with_capacity(3);
    push_length(&mut units, min_length, LengthUnit::MinLength);
    push_length(&mut units, max_length, LengthUnit::MaxLength);
    push_length(&mut units, length, LengthUnit::Length);
    Arc::new(units)
}

/// Walk length units only. A new `LengthUnit` variant fails to compile
/// here.
pub(crate) fn apply_length_units(units: &[LengthUnit], counted: usize) -> Result<(), FailKind> {
    for unit in units {
        let fail = match *unit {
            LengthUnit::MinLength(min) => (counted < min).then_some(FailKind::MinLength),
            LengthUnit::MaxLength(max) => (counted > max).then_some(FailKind::MaxLength),
            LengthUnit::Length(exact) => (counted != exact).then_some(FailKind::Length),
        };
        if let Some(kind) = fail {
            return Err(kind);
        }
    }
    Ok(())
}
