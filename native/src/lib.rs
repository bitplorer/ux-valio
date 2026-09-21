//! Optional apply peer for `ux-valio[native]`.
//!
//! Closed Integer and Float bound plans, closed String and Bytes length
//! plans, a closed IntegerEnum member-set plan, and a closed StringEnum
//! UTF-8 member-set plan. Type door is the FFI extract
//! (`apply_integer(plan, i64)` / `apply_float(plan, f64)` /
//! `apply_string(plan, &str)` / `apply_bytes(plan, &[u8])` /
//! `apply_integer_enum(plan, i64)` / `apply_string_enum(plan, &str)`).
//! Bound units (`MinValue` / `MaxValue` / `GreaterThan` / `LessThan` /
//! `Equal`) run after numeric extract. Length units (`MinLength` /
//! `MaxLength` / `Length`) are shared: String count is Unicode scalar
//! values (`chars().count()`), matching host `len(str)`; Bytes count is
//! `len()` of the extracted `&[u8]`, matching host `len(bytes)` — not
//! Unicode scalar values. IntegerEnum units are `Member(i64)` values
//! from the concrete `enum.IntEnum`; membership is exact `i64`
//! equality. StringEnum values are UTF-8 strings from the concrete
//! str-valued `enum.Enum`; membership is exact `&str` equality (no
//! casefold, no NFC). Host maps `FailKind` to KEEP wording. Open /
//! generic type checks stay on the host — this crate does not reflect
//! Python typing. Host compiles once at bind; each set is one FFI
//! apply. Soul stays on the host (descriptor, hooks, store). Not Cap
//! Door B.

use std::sync::Arc;

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
    /// Plan-shape marker. Type extract is the FFI `i64` argument.
    /// Host `isinstance` gates first against the concrete `enum.IntEnum`
    /// (so a plain `int` or another enum misses before extract).
    /// `None` / `collect_all` type miss stay host. Not an open type check.
    IntegerEnum,
    /// One `i64` member value of the concrete `enum.IntEnum`.
    /// Membership is exact equality with the extracted `i64`.
    Member(i64),
    /// Plan-shape marker. Type extract is the FFI `&str` argument: the
    /// member's `.value`, not the enum object. Host `isinstance` gates
    /// first against the concrete str-valued `enum.Enum`. `None` /
    /// `collect_all` type miss stay host. Not an open type check and
    /// not a String length plan. The UTF-8 set lives on `Plan`, not in
    /// this `Copy` unit.
    StringEnum,
}

/// Compiled plan. Built once; applied many times.
///
/// Owned unit list (`Arc<Vec<Unit>>`) so a single-bound plan and a
/// min+max range share one type — not a fixed two-slot array. Apply
/// clones the `Arc`, not the units. `string_members` is the shared
/// empty set except on a StringEnum plan.
#[pyclass(frozen)]
struct Plan {
    units: Arc<Vec<Unit>>,
    string_members: Arc<Vec<String>>,
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
    /// Host IntegerEnum / StringEnum type door: extracted scalar was not
    /// a compiled member value. Host formats the KEEP type-door
    /// `TypeError`.
    NotMember = 9,
}

/// Door A IEEE compares. `PartialOrd`/`PartialEq` match host Python:
/// NaN unordered (min/max/gt/lt pass), `nan != nan` (`eq` fails).
/// Do not use `total_cmp` — that would be a second policy. One compare
/// for `i64` and `f64`; the scalar type is the door.
#[allow(clippy::float_cmp)]
fn scalar_miss<T: PartialOrd>(kind: FailKind, value: T, bound: T) -> Option<FailKind> {
    let missed = match kind {
        FailKind::MinValue => value < bound,
        FailKind::MaxValue => value > bound,
        FailKind::GreaterThan => value <= bound,
        FailKind::LessThan => value >= bound,
        FailKind::Equal => value != bound,
        _ => false,
    };
    missed.then_some(kind)
}

fn miss(kind: FailKind, value: Bound, bound: Bound) -> Option<FailKind> {
    match (value, bound) {
        (Bound::Integer(value), Bound::Integer(bound)) => scalar_miss(kind, value, bound),
        (Bound::Float(value), Bound::Float(bound)) => scalar_miss(kind, value, bound),
        // Host never mixes doors; a mismatched payload is a no-op so
        // apply still returns Option<FailKind> (infra is host RuntimeError).
        _ => None,
    }
}

/// One empty member set for every plan that is not a StringEnum.
fn share_empty_members() -> Arc<Vec<String>> {
    static EMPTY: std::sync::LazyLock<Arc<Vec<String>>> =
        std::sync::LazyLock::new(|| Arc::new(Vec::new()));
    Arc::clone(&EMPTY)
}

fn share_plan(units: Vec<Unit>) -> Plan {
    Plan {
        units: Arc::new(units),
        string_members: share_empty_members(),
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
            // Enum member-set units belong on apply_integer_enum /
            // apply_string_enum.
            Unit::IntegerEnum | Unit::Member(_) | Unit::StringEnum => None,
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

fn compile_bound_plan<T>(
    shape: Unit,
    wrap: impl Fn(T) -> Bound + Copy,
    min_value: Option<T>,
    max_value: Option<T>,
    gt: Option<T>,
    lt: Option<T>,
    eq: Option<T>,
) -> Plan {
    // Shape marker plus the five host bound kwargs.
    let mut units = Vec::with_capacity(6);
    units.push(shape);
    // Host `_validate_value` order: min_value / gt, then max_value / lt, then eq.
    push_bound(&mut units, min_value, |v| Unit::MinValue(wrap(v)));
    push_bound(&mut units, gt, |v| Unit::GreaterThan(wrap(v)));
    push_bound(&mut units, max_value, |v| Unit::MaxValue(wrap(v)));
    push_bound(&mut units, lt, |v| Unit::LessThan(wrap(v)));
    push_bound(&mut units, eq, |v| Unit::Equal(wrap(v)));
    share_plan(units)
}

fn compile_integer_plan(
    min_value: Option<i64>,
    max_value: Option<i64>,
    gt: Option<i64>,
    lt: Option<i64>,
    eq: Option<i64>,
) -> Plan {
    compile_bound_plan(
        Unit::Integer,
        Bound::Integer,
        min_value,
        max_value,
        gt,
        lt,
        eq,
    )
}

fn compile_float_plan(
    min_value: Option<f64>,
    max_value: Option<f64>,
    gt: Option<f64>,
    lt: Option<f64>,
    eq: Option<f64>,
) -> Plan {
    compile_bound_plan(Unit::Float, Bound::Float, min_value, max_value, gt, lt, eq)
}

fn apply_length_units(units: &[Unit], counted: usize) -> Result<(), FailKind> {
    for unit in units {
        let fail = match *unit {
            Unit::String | Unit::Bytes => None,
            Unit::MinLength(min) => (counted < min).then_some(FailKind::MinLength),
            Unit::MaxLength(max) => (counted > max).then_some(FailKind::MaxLength),
            Unit::Length(exact) => (counted != exact).then_some(FailKind::Length),
            // Numeric and enum units belong on their own apply doors.
            // Exhaustive so a new unit is a compile error, not a silent pass.
            Unit::Integer
            | Unit::Float
            | Unit::MinValue(_)
            | Unit::MaxValue(_)
            | Unit::GreaterThan(_)
            | Unit::LessThan(_)
            | Unit::Equal(_)
            | Unit::IntegerEnum
            | Unit::Member(_)
            | Unit::StringEnum => None,
        };
        if let Some(kind) = fail {
            return Err(kind);
        }
    }
    Ok(())
}

fn apply_member_units(units: &[Unit], value: i64) -> Result<(), FailKind> {
    let found = units
        .iter()
        .any(|unit| matches!(*unit, Unit::Member(member) if member == value));
    if found {
        Ok(())
    } else {
        Err(FailKind::NotMember)
    }
}

fn compile_integer_enum_plan(members: Vec<i64>) -> Plan {
    let mut units = Vec::with_capacity(members.len() + 1);
    units.push(Unit::IntegerEnum);
    for member in members {
        units.push(Unit::Member(member));
    }
    share_plan(units)
}

fn compile_string_enum_plan(members: Vec<String>) -> Plan {
    Plan {
        units: Arc::new(vec![Unit::StringEnum]),
        string_members: Arc::new(members),
    }
}

fn apply_string_members(members: &[String], value: &str) -> Result<(), FailKind> {
    if members.iter().any(|member| member == value) {
        Ok(())
    } else {
        Err(FailKind::NotMember)
    }
}

fn compile_length_plan(
    shape: Unit,
    min_length: Option<usize>,
    max_length: Option<usize>,
    length: Option<usize>,
) -> Plan {
    // Shape marker plus min_length / max_length / length.
    let mut units = Vec::with_capacity(4);
    units.push(shape);
    // Host `_validate_length` order: min_length, max_length, exact length.
    push_bound(&mut units, min_length, Unit::MinLength);
    push_bound(&mut units, max_length, Unit::MaxLength);
    push_bound(&mut units, length, Unit::Length);
    share_plan(units)
}

/// Product peer: `compile_integer(...)` / `compile_float(...)` /
/// `compile_string(...)` / `compile_bytes(...)` /
/// `compile_integer_enum(...)` / `compile_string_enum(...)` + one-shot
/// `apply_integer` / `apply_float` / `apply_string` / `apply_bytes` /
/// `apply_integer_enum` / `apply_string_enum`.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. Plan shape is `Integer`,
/// `Float`, `String`, `Bytes`, `IntegerEnum`, or `StringEnum`; extract
/// is the FFI argument. Compile kwargs are host names (`min_value` /
/// `gt` / `max_length` / `length`) or `members` for an enum set, mapped
/// onto the full-word units. Not a taught L1 API. Compile and apply
/// stay separate doors.
#[pymodule]
mod ux_valio_native {
    use super::*;

    #[pymodule_export]
    use super::FailKind;

    #[pymodule_export]
    use super::Plan;

    /// Closed Integer bound plan. Omitted kwargs stay off the unit list.
    ///
    /// `compile_integer(5)` is still `MinValue(5)` (positional first arg).
    /// Range is `compile_integer(min_value=0, max_value=10)`. Host
    /// `gt`/`lt`/`eq` map to `GreaterThan` / `LessThan` / `Equal`.
    #[pyfunction]
    #[pyo3(signature = (min_value=None, max_value=None, gt=None, lt=None, eq=None))]
    fn compile_integer(
        min_value: Option<i64>,
        max_value: Option<i64>,
        gt: Option<i64>,
        lt: Option<i64>,
        eq: Option<i64>,
    ) -> Plan {
        compile_integer_plan(min_value, max_value, gt, lt, eq)
    }

    /// Closed Float bound plan. Omitted kwargs stay off the unit list.
    ///
    /// Same host kwarg names as `compile_integer`. `f64` extract is the
    /// Float door (`NaN` / `±inf` are values, not a second policy).
    #[pyfunction]
    #[pyo3(signature = (min_value=None, max_value=None, gt=None, lt=None, eq=None))]
    fn compile_float(
        min_value: Option<f64>,
        max_value: Option<f64>,
        gt: Option<f64>,
        lt: Option<f64>,
        eq: Option<f64>,
    ) -> Plan {
        compile_float_plan(min_value, max_value, gt, lt, eq)
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
    /// the plan body (`Python::detach`). The unit list is an `Arc`
    /// clone; the scalar is `i64`. Not an open type check.
    #[pyfunction]
    fn apply_integer(py: Python<'_>, plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        let units = Arc::clone(&plan.units);
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
        let units = Arc::clone(&plan.units);
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
        let units = Arc::clone(&plan.units);
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
        let units = Arc::clone(&plan.units);
        let byte_len = value.len();
        py.detach(move || apply_length_units(&units, byte_len).err())
    }

    /// Closed IntegerEnum member-set plan. `members` are the concrete
    /// `enum.IntEnum` `i64` values (host order). An empty list is an
    /// empty set: every apply is `NotMember`. Host does not compile an
    /// empty set. Not a taught L1 kwarg.
    #[pyfunction]
    fn compile_integer_enum(members: Vec<i64>) -> Plan {
        compile_integer_enum_plan(members)
    }

    /// One-shot IntegerEnum apply. Success is `None`; a value outside
    /// the compiled member set is `FailKind::NotMember`.
    ///
    /// Closed IntegerEnum type door is this `i64` extract. A Python int
    /// outside i64 raises `OverflowError` at this FFI boundary; host
    /// falls through to the host type door. Membership is exact `i64`
    /// equality with `Member` units (not an open type check). Releases
    /// the GIL (`Python::detach`) for the unit walk.
    #[pyfunction]
    fn apply_integer_enum(py: Python<'_>, plan: PyRef<'_, Plan>, value: i64) -> Option<FailKind> {
        let units = Arc::clone(&plan.units);
        py.detach(move || apply_member_units(&units, value).err())
    }

    /// Closed StringEnum member-set plan. `members` are the concrete
    /// str-valued enum `.value` strings (host order, UTF-8). An empty
    /// list is an empty set: every apply is `NotMember`. Host does not
    /// compile an empty set or a value that is not UTF-8. Not a taught
    /// L1 kwarg. Not a String length plan.
    #[pyfunction]
    fn compile_string_enum(members: Vec<String>) -> Plan {
        compile_string_enum_plan(members)
    }

    /// One-shot StringEnum apply. Success is `None`; a value outside
    /// the compiled member set is `FailKind::NotMember`.
    ///
    /// Closed StringEnum type door is this `&str` extract (the member's
    /// `.value`). A Python `str` that is not UTF-8 raises
    /// `UnicodeEncodeError` at this FFI boundary; host falls through to
    /// the host type door. Membership is exact UTF-8 equality with the
    /// compiled strings (no casefold, no NFC). Releases the GIL
    /// (`Python::detach`) for the walk. The member set is an `Arc`
    /// clone; the query is one owned `String` so the walk does not
    /// borrow Python.
    #[pyfunction]
    fn apply_string_enum(py: Python<'_>, plan: PyRef<'_, Plan>, value: &str) -> Option<FailKind> {
        let members = Arc::clone(&plan.string_members);
        let owned = value.to_owned();
        py.detach(move || apply_string_members(&members, &owned).err())
    }
}
