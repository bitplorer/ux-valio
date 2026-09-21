//! Optional apply peer for `ux-valio[native]`.
//!
//! Closed Integer and Float bound plans plus closed String and Bytes
//! length plans. Type door is the FFI extract (`apply(plan, i64)` /
//! `apply_float(plan, f64)` / `apply_string(plan, &str)` /
//! `apply_bytes(plan, &[u8])`). Bound units (`MinValue` / `MaxValue` /
//! `GreaterThan` / `LessThan` / `Equal`) run after numeric extract.
//! Length units (`MinLength` / `MaxLength` / `Length`) are shared:
//! String count is Unicode scalar values (`chars().count()`), matching
//! host `len(str)`; Bytes count is `len()` of the extracted `&[u8]`,
//! matching host `len(bytes)` — not Unicode scalar values.
//! Host maps `FailKind` to KEEP wording. Open / generic type checks
//! stay on the host — this crate does not reflect Python typing. Host
//! compiles once at bind; each set is one FFI apply. Soul stays on the
//! host (descriptor, hooks, store). Not Cap Door B.

use pyo3::prelude::*;

/// Bound payload. Integer plans carry `i64`; Float plans carry `f64`.
/// Family names (`MinValue` / …) stay shared; the scalar is the door.
#[derive(Clone, Copy)]
enum Bound {
    Integer(i64),
    Float(f64),
}

/// Specified scalar units. `Integer` / `Float` / `String` / `Bytes` are
/// plan-shape markers, not open type checks. Type is the FFI extract;
/// bound or length units follow.
#[derive(Clone, Copy)]
enum Unit {
    /// Plan-shape marker. Type extract is the FFI `i64` argument, not an
    /// open type check. Host `isinstance` gates first so Python `True`
    /// is `int` (load-bearing); `None` / `collect_all` type miss stay
    /// host.
    Integer,
    /// Plan-shape marker. Type extract is the FFI `f64` argument.
    /// Host `isinstance` gates first so Python `int` / `bool` miss
    /// Float (KEEP); `None` / `collect_all` type miss stay host.
    /// NaN / ±inf are valid `float` values — IEEE compare, no second
    /// policy (Door A: `nan < bound` is false, so min/max/gt/lt pass;
    /// `nan != bound` is true even when `bound` is NaN, so `eq` fails).
    Float,
    /// Host `min_value`, inclusive ≥.
    MinValue(Bound),
    /// Host `max_value`, inclusive ≤.
    MaxValue(Bound),
    /// Host `gt`, exclusive >.
    GreaterThan(Bound),
    /// Host `lt`, exclusive <.
    LessThan(Bound),
    /// Host `eq`/`value`, exact. IEEE `!=` so NaN never equals NaN.
    Equal(Bound),
    /// Plan-shape marker. Type extract is the FFI `&str` argument.
    /// Host `isinstance` gates first so Python `bytes` miss String
    /// (KEEP); `None` / `collect_all` type miss stay host.
    String,
    /// Plan-shape marker. Type extract is the FFI `&[u8]` argument.
    /// Host `isinstance` gates first so Python `str` / `bytearray`
    /// miss Bytes (KEEP); `None` / `collect_all` type miss stay host.
    Bytes,
    /// Host `min_length`, inclusive. String count is Unicode scalar
    /// values; Bytes count is the extracted `&[u8]` length.
    MinLength(usize),
    /// Host `max_length`, inclusive. String count is Unicode scalar
    /// values; Bytes count is the extracted `&[u8]` length.
    MaxLength(usize),
    /// Host exact `length`. String count is Unicode scalar values;
    /// Bytes count is the extracted `&[u8]` length.
    Length(usize),
}

/// Compiled plan. Built once; applied many times.
///
/// Owned `Vec` so a single-bound plan and a min+max range share one
/// type — not a fixed two-slot array.
#[pyclass(frozen)]
struct Plan {
    units: Vec<Unit>,
}

/// Small error kind. Host formats KEEP messages via the FailKind map.
/// Type misses never leave the host (`isinstance` before apply — Python
/// `True` is `int`; Python `int` is not `float`). Bound units run after
/// the scalar extract.
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
    /// Host `min_length`: count was less than the inclusive bound.
    /// String: codepoints. Bytes: `len(bytes)`.
    MinLength = 6,
    /// Host `max_length`: count was greater than the inclusive bound.
    /// String: codepoints. Bytes: `len(bytes)`.
    MaxLength = 7,
    /// Host exact `length`: count was not the compiled length.
    /// String: codepoints. Bytes: `len(bytes)`.
    Length = 8,
}

/// Door A IEEE compares. `PartialOrd`/`PartialEq` on `f64` match host
/// Python: NaN unordered (min/max/gt/lt pass), `nan != nan` (`eq` fails).
/// Do not use `total_cmp` — that would be a second policy.
#[allow(clippy::float_cmp)]
fn miss(kind: FailKind, value: Bound, bound: Bound) -> Option<FailKind> {
    match (value, bound) {
        (Bound::Integer(value), Bound::Integer(bound)) => match kind {
            FailKind::MinValue if value < bound => Some(kind),
            FailKind::MaxValue if value > bound => Some(kind),
            FailKind::GreaterThan if value <= bound => Some(kind),
            FailKind::LessThan if value >= bound => Some(kind),
            FailKind::Equal if value != bound => Some(kind),
            _ => None,
        },
        (Bound::Float(value), Bound::Float(bound)) => match kind {
            FailKind::MinValue if value < bound => Some(kind),
            FailKind::MaxValue if value > bound => Some(kind),
            FailKind::GreaterThan if value <= bound => Some(kind),
            FailKind::LessThan if value >= bound => Some(kind),
            FailKind::Equal if value != bound => Some(kind),
            _ => None,
        },
        // Host never mixes doors; a mismatched payload is a no-op so
        // apply still returns Option<FailKind> (infra is host RuntimeError).
        _ => None,
    }
}

fn apply_units(units: &[Unit], value: Bound) -> Result<(), FailKind> {
    for unit in units {
        let fail = match *unit {
            Unit::Integer | Unit::Float | Unit::String | Unit::Bytes => None,
            Unit::MinValue(bound) => miss(FailKind::MinValue, value, bound),
            Unit::MaxValue(bound) => miss(FailKind::MaxValue, value, bound),
            Unit::GreaterThan(bound) => miss(FailKind::GreaterThan, value, bound),
            Unit::LessThan(bound) => miss(FailKind::LessThan, value, bound),
            Unit::Equal(bound) => miss(FailKind::Equal, value, bound),
            // Length units belong on apply_string / apply_bytes; numeric apply
            // no-ops them (host never mixes doors).
            Unit::MinLength(_) | Unit::MaxLength(_) | Unit::Length(_) => None,
        };
        if let Some(kind) = fail {
            return Err(kind);
        }
    }
    Ok(())
}

fn push_bound<T>(units: &mut Vec<Unit>, bound: Option<T>, unit: impl FnOnce(T) -> Unit) {
    if let Some(value) = bound {
        units.push(unit(value));
    }
}

fn compile_plan<T>(
    shape: Unit,
    wrap: impl Fn(T) -> Bound + Copy,
    min_value: Option<T>,
    max_value: Option<T>,
    gt: Option<T>,
    lt: Option<T>,
    eq: Option<T>,
) -> Plan {
    let mut units = Vec::with_capacity(4);
    units.push(shape);
    // Host `_validate_value` order: min_value / gt, then max_value / lt, then eq.
    push_bound(&mut units, min_value, |v| Unit::MinValue(wrap(v)));
    push_bound(&mut units, gt, |v| Unit::GreaterThan(wrap(v)));
    push_bound(&mut units, max_value, |v| Unit::MaxValue(wrap(v)));
    push_bound(&mut units, lt, |v| Unit::LessThan(wrap(v)));
    push_bound(&mut units, eq, |v| Unit::Equal(wrap(v)));
    Plan { units }
}

fn apply_length_units(units: &[Unit], counted: usize) -> Result<(), FailKind> {
    for unit in units {
        let fail = match *unit {
            Unit::String | Unit::Bytes => None,
            Unit::MinLength(min) if counted < min => Some(FailKind::MinLength),
            Unit::MinLength(_) => None,
            Unit::MaxLength(max) if counted > max => Some(FailKind::MaxLength),
            Unit::MaxLength(_) => None,
            Unit::Length(exact) if counted != exact => Some(FailKind::Length),
            Unit::Length(_) => None,
            // Numeric units belong on apply / apply_float; host never mixes.
            _ => None,
        };
        if let Some(kind) = fail {
            return Err(kind);
        }
    }
    Ok(())
}

fn compile_length_plan(
    shape: Unit,
    min_length: Option<usize>,
    max_length: Option<usize>,
    length: Option<usize>,
) -> Plan {
    let mut units = Vec::with_capacity(4);
    units.push(shape);
    // Host `_validate_length` order: min_length, max_length, exact length.
    push_bound(&mut units, min_length, Unit::MinLength);
    push_bound(&mut units, max_length, Unit::MaxLength);
    push_bound(&mut units, length, Unit::Length);
    Plan { units }
}

/// Product peer: `compile(...)` / `compile_float(...)` /
/// `compile_string(...)` / `compile_bytes(...)` + one-shot apply.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. Plan shape is `Integer`,
/// `Float`, `String`, or `Bytes`; extract is the FFI argument. Compile
/// kwargs are host names (`min_value` / `gt` / `max_length` / `length`)
/// mapped onto the full-word units. Not a taught L1 API.
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
        compile_plan(
            Unit::Integer,
            Bound::Integer,
            min_value,
            max_value,
            gt,
            lt,
            eq,
        )
    }

    /// Closed Float bound plan. Omitted kwargs stay off the unit list.
    ///
    /// Same host kwarg names as `compile`. `f64` extract is the Float
    /// door (`NaN` / `±inf` are values, not a second policy).
    #[pyfunction]
    #[pyo3(signature = (min_value=None, max_value=None, gt=None, lt=None, eq=None))]
    fn compile_float(
        min_value: Option<f64>,
        max_value: Option<f64>,
        gt: Option<f64>,
        lt: Option<f64>,
        eq: Option<f64>,
    ) -> Plan {
        compile_plan(Unit::Float, Bound::Float, min_value, max_value, gt, lt, eq)
    }

    /// Closed String length plan. Omitted kwargs stay off the unit list.
    ///
    /// Host kwargs stay `min_length` / `max_length` / `length`. Units are
    /// `MinLength` / `MaxLength` / `Length` (usize). Count at apply is
    /// Unicode scalar values (`chars().count()`), matching host `len(str)`.
    #[pyfunction]
    #[pyo3(signature = (min_length=None, max_length=None, length=None))]
    fn compile_string(
        min_length: Option<usize>,
        max_length: Option<usize>,
        length: Option<usize>,
    ) -> Plan {
        compile_length_plan(Unit::String, min_length, max_length, length)
    }

    /// Closed Bytes length plan. Omitted kwargs stay off the unit list.
    ///
    /// Host kwargs stay `min_length` / `max_length` / `length`. Units are
    /// the same `MinLength` / `MaxLength` / `Length` (usize) as String.
    /// Count at apply is `len()` of the extracted `&[u8]`, matching host
    /// `len(bytes)` — not Unicode scalar values.
    #[pyfunction]
    #[pyo3(signature = (min_length=None, max_length=None, length=None))]
    fn compile_bytes(
        min_length: Option<usize>,
        max_length: Option<usize>,
        length: Option<usize>,
    ) -> Plan {
        compile_length_plan(Unit::Bytes, min_length, max_length, length)
    }

    /// One-shot Integer apply. Success is `None`; bound miss is a `FailKind`.
    ///
    /// Closed Integer type door is this `i64` extract (range oracle too:
    /// a Python int outside i64 raises `OverflowError`; host falls
    /// through). Bound units run after extract. Releases the GIL for
    /// the plan body (`Python::detach`). The plan is an owned clone of
    /// `Copy` units; the scalar is `i64`. Not an open type check.
    #[pyfunction]
    fn apply(py: Python<'_>, plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        let units = plan.units.clone();
        py.detach(move || apply_units(&units, Bound::Integer(value)).err())
    }

    /// One-shot Float apply. Success is `None`; bound miss is a `FailKind`.
    ///
    /// Closed Float type door is this `f64` extract. A Python value that
    /// cannot extract as `f64` raises at this FFI boundary (`OverflowError`
    /// or extract TypeError); host falls through to `ValueValidator`.
    /// Bound units run after extract. IEEE compare (Door A): NaN is
    /// unordered, so min/max/gt/lt pass; `eq` uses `!=` so NaN never
    /// matches. Releases the GIL (`Python::detach`).
    #[pyfunction]
    fn apply_float(py: Python<'_>, plan: PyRef<'_, Plan>, value: f64) -> Option<FailKind> {
        let units = plan.units.clone();
        py.detach(move || apply_units(&units, Bound::Float(value)).err())
    }

    /// One-shot String apply. Success is `None`; length miss is a `FailKind`.
    ///
    /// Closed String type door is this `&str` extract. A Python value
    /// that cannot extract as UTF-8 (lone surrogates) raises at this FFI
    /// boundary; host falls through to `LengthValidator`. Length units
    /// run after extract. Count is Unicode scalar values
    /// (`chars().count()`), matching host `len(str)` — not UTF-8 byte
    /// length. Releases the GIL (`Python::detach`) for the unit walk.
    #[pyfunction]
    fn apply_string(py: Python<'_>, plan: PyRef<'_, Plan>, value: &str) -> Option<FailKind> {
        let units = plan.units.clone();
        let char_len = value.chars().count();
        py.detach(move || apply_length_units(&units, char_len).err())
    }

    /// One-shot Bytes apply. Success is `None`; length miss is a `FailKind`.
    ///
    /// Closed Bytes type door is this `&[u8]` extract. A Python value
    /// that cannot extract as bytes raises at this FFI boundary
    /// (`OverflowError` or extract TypeError); host falls through to
    /// `LengthValidator`. Length units run after extract. Count is
    /// `value.len()`, matching host `len(bytes)` — not Unicode
    /// scalar values. Releases the GIL
    /// (`Python::detach`) for the unit walk.
    #[pyfunction]
    fn apply_bytes(py: Python<'_>, plan: PyRef<'_, Plan>, value: &[u8]) -> Option<FailKind> {
        let units = plan.units.clone();
        let byte_len = value.len();
        py.detach(move || apply_length_units(&units, byte_len).err())
    }
}
