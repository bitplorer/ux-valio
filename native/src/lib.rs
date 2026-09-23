//! Optional product PyO3 native module for `ux-valio[native]`.
//!
//! [`plan::Plan`] is one variant per family. The variant owns that
//! family's checks: Integer / Float own [`bound::BoundUnit`] values,
//! String / Bytes own [`length::LengthUnit`] values, IntegerEnum owns
//! an `i64` member set, StringEnum owns a UTF-8 member set, Boolean,
//! Decimal, Date, DateTime, and Uuid are type-door markers. `apply_integer`
//! clones the integer
//! bounds and walks those — a length unit is the wrong type, so it
//! cannot be passed into that walk.
//!
//! Type door is the FFI extract (`apply_integer(plan, i64)` /
//! `apply_float(plan, f64)` / `apply_string(plan, &str)` /
//! `apply_bytes(plan, &[u8])` / `apply_integer_enum(plan, i64)` /
//! `apply_string_enum(plan, &str)` / `apply_boolean(plan, bool)` /
//! `apply_decimal(plan, decimal.Decimal)` /
//! `apply_date(plan, datetime.date)` /
//! `apply_datetime(plan, datetime.datetime)` /
//! `apply_uuid(plan, uuid.UUID)`).
//! Bound units (`MinValue` / `MaxValue` / `GreaterThan` / `LessThan` /
//! `Equal`) run after numeric extract. Each miss arm is fail-when:
//! `min_value` passes when `value >= bound` (miss `<`); `gt` passes
//! when `value > bound` (miss `<=`, exclusive); `max_value` passes when
//! `value <= bound` (miss `>`); `lt` passes when `value < bound` (miss
//! `>=`, exclusive); `eq` passes when equal (miss `!=`; NaN never
//! equals). Length units (`MinLength` /
//! `MaxLength` / `Length`) are shared: String count is Unicode scalar
//! values (`chars().count()`), matching host `len(str)`; Bytes count is
//! `len()` of the extracted `&[u8]`, matching host `len(bytes)`.
//! IntegerEnum membership is exact `i64` equality. StringEnum membership
//! is exact `&str` equality (no casefold, no NFC). Host maps `FailKind`
//! to KEEP wording. Open / generic type checks stay on the host — this
//! crate does not reflect Python typing. Host compiles once at bind;
//! each set is one FFI apply. Soul stays on the host (descriptor, hooks,
//! store). Not Cap Door B.

use std::sync::Arc;

use pyo3::prelude::*;

use bound::{apply_bound_units, compile_bound_plan};
use length::{apply_length_units, compile_length_plan};
use plan::{
    apply_i64_members, apply_str_members, share_plan, unexpected_family, FailKind, Plan, PyPlan,
};

mod bound;
mod length;
mod plan;

/// Exact `decimal.Decimal`. Not `f64`. Not a string coerce.
struct ExtractedDecimal;

fn cached_decimal_type(py: Python<'_>) -> PyResult<pyo3::Bound<'_, PyAny>> {
    use pyo3::sync::PyOnceLock;

    static DECIMAL: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
    let cached = DECIMAL.get_or_try_init(py, || {
        Ok::<_, PyErr>(py.import("decimal")?.getattr("Decimal")?.unbind())
    })?;
    Ok(cached.bind(py).clone())
}

impl<'a, 'py> FromPyObject<'a, 'py> for ExtractedDecimal {
    type Error = PyErr;

    fn extract(obj: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        let decimal_type = cached_decimal_type(obj.py())?;
        if obj.is_instance(&decimal_type)? {
            Ok(ExtractedDecimal)
        } else {
            Err(decimal_extract_error(obj.py()))
        }
    }
}

/// Extract miss is a Python `TypeError`. Built from the builtin so this
/// file does not name a reflected type object. Host `isinstance` misses
/// first; this is the bridge for a direct `apply_decimal` call.
fn decimal_extract_error(py: Python<'_>) -> PyErr {
    extract_type_error(py, "decimal.Decimal")
}

/// Exact `datetime.date`. `datetime.datetime` is a subclass and extracts.
/// Not a string coerce.
struct ExtractedDate;

/// Exact `datetime.datetime`. A plain `datetime.date` does not extract.
/// Not a string coerce.
struct ExtractedDateTime;

fn cached_datetime_attr<'py>(
    py: Python<'py>,
    name: &'static str,
    slot: &'static pyo3::sync::PyOnceLock<Py<PyAny>>,
) -> PyResult<pyo3::Bound<'py, PyAny>> {
    let cached = slot.get_or_try_init(py, || {
        Ok::<_, PyErr>(py.import("datetime")?.getattr(name)?.unbind())
    })?;
    Ok(cached.bind(py).clone())
}

fn cached_date_type(py: Python<'_>) -> PyResult<pyo3::Bound<'_, PyAny>> {
    use pyo3::sync::PyOnceLock;

    static DATE: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
    cached_datetime_attr(py, "date", &DATE)
}

fn cached_datetime_type(py: Python<'_>) -> PyResult<pyo3::Bound<'_, PyAny>> {
    use pyo3::sync::PyOnceLock;

    static DATETIME: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
    cached_datetime_attr(py, "datetime", &DATETIME)
}

impl<'a, 'py> FromPyObject<'a, 'py> for ExtractedDate {
    type Error = PyErr;

    fn extract(obj: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        let date_type = cached_date_type(obj.py())?;
        if obj.is_instance(&date_type)? {
            Ok(ExtractedDate)
        } else {
            Err(extract_type_error(obj.py(), "datetime.date"))
        }
    }
}

impl<'a, 'py> FromPyObject<'a, 'py> for ExtractedDateTime {
    type Error = PyErr;

    fn extract(obj: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        let datetime_type = cached_datetime_type(obj.py())?;
        if obj.is_instance(&datetime_type)? {
            Ok(ExtractedDateTime)
        } else {
            Err(extract_type_error(obj.py(), "datetime.datetime"))
        }
    }
}

/// Exact `uuid.UUID`. Not a string coerce.
struct ExtractedUuid;

fn cached_uuid_type(py: Python<'_>) -> PyResult<pyo3::Bound<'_, PyAny>> {
    use pyo3::sync::PyOnceLock;

    static UUID: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
    let cached = UUID.get_or_try_init(py, || {
        Ok::<_, PyErr>(py.import("uuid")?.getattr("UUID")?.unbind())
    })?;
    Ok(cached.bind(py).clone())
}

impl<'a, 'py> FromPyObject<'a, 'py> for ExtractedUuid {
    type Error = PyErr;

    fn extract(obj: Borrowed<'a, 'py, PyAny>) -> Result<Self, Self::Error> {
        let uuid_type = cached_uuid_type(obj.py())?;
        if obj.is_instance(&uuid_type)? {
            Ok(ExtractedUuid)
        } else {
            Err(extract_type_error(obj.py(), "uuid.UUID"))
        }
    }
}

/// Extract miss is a Python `TypeError`. Built from the builtin so this
/// file does not name a reflected type object. Host `isinstance` misses
/// first; this is the bridge for a direct `apply_*` call.
fn extract_type_error(py: Python<'_>, expected: &str) -> PyErr {
    let cls = match py
        .import("builtins")
        .and_then(|builtins| builtins.getattr("TypeError"))
    {
        Ok(cls) => cls,
        Err(err) => return err,
    };
    match cls.call1((format!("argument 'value': expected {expected}"),)) {
        Ok(err) => PyErr::from_value(err),
        Err(err) => err,
    }
}

fn compile_integer_plan(
    min_value: Option<i64>,
    max_value: Option<i64>,
    gt: Option<i64>,
    lt: Option<i64>,
    eq: Option<i64>,
) -> PyPlan {
    share_plan(Plan::Integer(compile_bound_plan(
        min_value, max_value, gt, lt, eq,
    )))
}

fn compile_float_plan(
    min_value: Option<f64>,
    max_value: Option<f64>,
    gt: Option<f64>,
    lt: Option<f64>,
    eq: Option<f64>,
) -> PyPlan {
    share_plan(Plan::Float(compile_bound_plan(
        min_value, max_value, gt, lt, eq,
    )))
}

fn compile_integer_enum_plan(members: Vec<i64>) -> PyPlan {
    share_plan(Plan::IntegerEnum(Arc::new(members)))
}

fn compile_string_enum_plan(members: Vec<String>) -> PyPlan {
    share_plan(Plan::StringEnum(Arc::new(members)))
}

fn compile_boolean_plan() -> PyPlan {
    share_plan(Plan::Boolean)
}

fn compile_decimal_plan() -> PyPlan {
    share_plan(Plan::Decimal)
}

fn compile_date_plan() -> PyPlan {
    share_plan(Plan::Date)
}

fn compile_datetime_plan() -> PyPlan {
    share_plan(Plan::DateTime)
}

fn compile_uuid_plan() -> PyPlan {
    share_plan(Plan::Uuid)
}

/// Product native module: `compile_integer(...)` / `compile_float(...)` /
/// `compile_string(...)` / `compile_bytes(...)` /
/// `compile_integer_enum(...)` / `compile_string_enum(...)` /
/// `compile_boolean()` / `compile_decimal()` / `compile_date()` /
/// `compile_datetime()` / `compile_uuid()` + one-shot `apply_integer` /
/// `apply_float` / `apply_string` / `apply_bytes` / `apply_integer_enum` /
/// `apply_string_enum` / `apply_boolean` / `apply_decimal` /
/// `apply_date` / `apply_datetime` / `apply_uuid`.
///
/// `None` is `Ok(())`. A `FailKind` is `Err`. Plan shape is the [`Plan`]
/// variant; extract is the FFI argument. Compile kwargs are host names
/// (`min_value` / `gt` / `max_length` / `length`) or `members` for an
/// enum set. Boolean, Decimal, Date, DateTime, and Uuid take no kwargs.
/// Decimal extract is exact `decimal.Decimal` (no float bridge, no scale
/// unit). Date extract is `datetime.date` (`datetime.datetime` extracts
/// because it subclasses `date`). DateTime extract is
/// `datetime.datetime` (a plain `date` does not). Uuid extract is
/// exact `uuid.UUID` (a raw `str` does not). String coerce stays
/// host. Not a taught L1 API. Compile and apply stay separate doors. A
/// plan handed to another family's apply raises `RuntimeError` (the
/// walk is not run).
#[pymodule]
mod ux_valio_native {
    use super::*;

    #[pymodule_export]
    use super::FailKind;

    #[pymodule_export]
    use super::PyPlan;

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
    ) -> PyPlan {
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
    ) -> PyPlan {
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
    ) -> PyPlan {
        share_plan(Plan::String(compile_length_plan(
            min_length, max_length, length,
        )))
    }

    /// Closed Bytes length plan. Omitted kwargs stay off the unit list.
    ///
    /// Host kwargs stay `min_length` / `max_length` / `length`. Units are
    /// the same `MinLength` / `MaxLength` / `Length` (usize) as String.
    /// Count at apply is `len()` of the extracted `&[u8]`, matching host
    /// `len(bytes)`.
    #[pyfunction]
    #[pyo3(signature = (min_length=None, max_length=None, length=None))]
    fn compile_bytes(
        min_length: Option<usize>,
        max_length: Option<usize>,
        length: Option<usize>,
    ) -> PyPlan {
        share_plan(Plan::Bytes(compile_length_plan(
            min_length, max_length, length,
        )))
    }

    /// One-shot Integer apply. Success is `None`; bound miss is a `FailKind`.
    ///
    /// Closed Integer type door is this `i64` extract (range oracle too:
    /// a Python int outside i64 raises `OverflowError`; host falls
    /// through). Bound units run after extract. Releases the GIL for
    /// the plan body (`Python::detach`). The unit list is an `Arc`
    /// clone; the scalar is `i64`. Another family's plan is
    /// `RuntimeError` before the walk.
    #[pyfunction]
    fn apply_integer(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: i64,
    ) -> PyResult<Option<FailKind>> {
        let units = match &plan.body {
            Plan::Integer(units) => Arc::clone(units),
            Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_integer")),
        };
        Ok(py.detach(move || apply_bound_units(&units, value).err()))
    }

    /// One-shot Float apply. Success is `None`; bound miss is a `FailKind`.
    ///
    /// Closed Float type door is this `f64` extract. A Python value that
    /// cannot extract as `f64` raises at this FFI boundary (`OverflowError`
    /// or extract TypeError); host falls through to `ValueValidator`.
    /// Bound units run after extract. IEEE compare (Door A): NaN is
    /// unordered, so every fail-when compare (`<`, `>`, `<=`, `>=`) is
    /// false and min/max/gt/lt pass; `eq` uses `!=` so NaN never
    /// matches. `gt` still misses on `<=` and `lt` on `>=` for ordered
    /// values. Releases the GIL (`Python::detach`).
    #[pyfunction]
    fn apply_float(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: f64,
    ) -> PyResult<Option<FailKind>> {
        let units = match &plan.body {
            Plan::Float(units) => Arc::clone(units),
            Plan::Integer(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_float")),
        };
        Ok(py.detach(move || apply_bound_units(&units, value).err()))
    }

    /// One-shot String apply. Success is `None`; length miss is a `FailKind`.
    ///
    /// Closed String type door is this `&str` extract. A Python value
    /// that cannot extract as UTF-8 (lone surrogates) raises at this FFI
    /// boundary; host falls through to `LengthValidator`. Length units
    /// run after extract. Count is Unicode scalar values
    /// (`chars().count()`), matching host `len(str)`. Releases the GIL
    /// (`Python::detach`) for the unit walk.
    #[pyfunction]
    fn apply_string(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: &str,
    ) -> PyResult<Option<FailKind>> {
        let units = match &plan.body {
            Plan::String(units) => Arc::clone(units),
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_string")),
        };
        let char_len = value.chars().count();
        Ok(py.detach(move || apply_length_units(&units, char_len).err()))
    }

    /// One-shot Bytes apply. Success is `None`; length miss is a `FailKind`.
    ///
    /// Closed Bytes type door is this `&[u8]` extract. A Python value
    /// that cannot extract as bytes raises at this FFI boundary
    /// (`OverflowError` or extract TypeError); host falls through to
    /// `LengthValidator`. Length units run after extract. Count is
    /// `value.len()`, matching host `len(bytes)`. Releases the GIL
    /// (`Python::detach`) for the unit walk.
    #[pyfunction]
    fn apply_bytes(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: &[u8],
    ) -> PyResult<Option<FailKind>> {
        let units = match &plan.body {
            Plan::Bytes(units) => Arc::clone(units),
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_bytes")),
        };
        let byte_len = value.len();
        Ok(py.detach(move || apply_length_units(&units, byte_len).err()))
    }

    /// Closed IntegerEnum member-set plan. `members` are the concrete
    /// `enum.IntEnum` `i64` values (host order). An empty list is an
    /// empty set: every apply is `NotMember`. Host does not compile an
    /// empty set. Not a taught L1 kwarg.
    #[pyfunction]
    fn compile_integer_enum(members: Vec<i64>) -> PyPlan {
        compile_integer_enum_plan(members)
    }

    /// One-shot IntegerEnum apply. Success is `None`; a value outside
    /// the compiled member set is `FailKind::NotMember`.
    ///
    /// Closed IntegerEnum type door is this `i64` extract. A Python int
    /// outside i64 raises `OverflowError` at this FFI boundary; host
    /// falls through to the host type door. Membership is exact `i64`
    /// equality with the compiled member values. Releases the GIL
    /// (`Python::detach`) for the walk.
    #[pyfunction]
    fn apply_integer_enum(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: i64,
    ) -> PyResult<Option<FailKind>> {
        let members = match &plan.body {
            Plan::IntegerEnum(members) => Arc::clone(members),
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_integer_enum")),
        };
        Ok(py.detach(move || apply_i64_members(&members, value).err()))
    }

    /// Closed StringEnum member-set plan. `members` are the concrete
    /// str-valued enum `.value` strings (host order, UTF-8). An empty
    /// list is an empty set: every apply is `NotMember`. Host does not
    /// compile an empty set or a value that is not UTF-8. Not a taught
    /// L1 kwarg. Not a String length plan.
    #[pyfunction]
    fn compile_string_enum(members: Vec<String>) -> PyPlan {
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
    fn apply_string_enum(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: &str,
    ) -> PyResult<Option<FailKind>> {
        let members = match &plan.body {
            Plan::StringEnum(members) => Arc::clone(members),
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_string_enum")),
        };
        let owned = value.to_owned();
        Ok(py.detach(move || apply_str_members(&members, &owned).err()))
    }

    /// Closed Boolean type-door plan. No kwargs. The variant is the
    /// `Boolean` marker. Not a taught L1 API. Not an Integer plan
    /// (`bool` is `int` on the host Integer door; this door is exact
    /// `bool`).
    #[pyfunction]
    fn compile_boolean() -> PyPlan {
        compile_boolean_plan()
    }

    /// One-shot Boolean apply. Success is `None` for `True` and `False`.
    ///
    /// Closed Boolean type door is this `bool` extract. A Python `int`
    /// (`1` / `0`), `str`, or other non-bool raises at this FFI boundary
    /// (extract error); host falls through to the host type door. No
    /// coerce. No bound unit. Releases the GIL (`Python::detach`).
    /// Compile and apply stay a pair.
    #[pyfunction]
    fn apply_boolean(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: bool,
    ) -> PyResult<Option<FailKind>> {
        match &plan.body {
            Plan::Boolean => {}
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_boolean")),
        }
        let _ = value;
        Ok(py.detach(|| None))
    }

    /// Closed Decimal type-door plan. No kwargs. The variant is the
    /// `Decimal` marker. Not a taught L1 API. Not a Float plan
    /// (no `f64` bridge) and not a scale plan.
    #[pyfunction]
    fn compile_decimal() -> PyPlan {
        compile_decimal_plan()
    }

    /// One-shot Decimal apply. Success is `None` for an exact
    /// `decimal.Decimal`, including zero.
    ///
    /// Closed Decimal type door is this extract. A Python `float`,
    /// `int`, `bool`, or raw `str` raises at this FFI boundary (extract
    /// error); host falls through to the host type door. No coerce. No
    /// `Decimal(float)`. No scale unit. Releases the GIL
    /// (`Python::detach`). Compile and apply stay a pair.
    #[pyfunction]
    fn apply_decimal(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: ExtractedDecimal,
    ) -> PyResult<Option<FailKind>> {
        match &plan.body {
            Plan::Decimal => {}
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Date
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_decimal")),
        }
        let _ = value;
        Ok(py.detach(|| None))
    }

    /// Closed Date type-door plan. No kwargs. The variant is the
    /// `Date` marker. Not a taught L1 API. Not a DateTime plan.
    /// String coerce stays on the host.
    #[pyfunction]
    fn compile_date() -> PyPlan {
        compile_date_plan()
    }

    /// One-shot Date apply. Success is `None` for a `datetime.date`,
    /// including a `datetime.datetime` (it subclasses `date`).
    ///
    /// Closed Date type door is this extract. A Python `int`, `str`,
    /// `bool`, or other non-date raises at this FFI boundary (extract
    /// error); host falls through to the host type door. No string
    /// coerce. No bound unit. `DateValidator` still rejects
    /// `datetime.datetime` in the named extra after this door.
    /// Releases the GIL (`Python::detach`). Compile and apply stay a
    /// pair.
    #[pyfunction]
    fn apply_date(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: ExtractedDate,
    ) -> PyResult<Option<FailKind>> {
        match &plan.body {
            Plan::Date => {}
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::DateTime
            | Plan::Uuid => return Err(unexpected_family("apply_date")),
        }
        let _ = value;
        Ok(py.detach(|| None))
    }

    /// Closed DateTime type-door plan. No kwargs. The variant is the
    /// `DateTime` marker. Not a taught L1 API. Not a Date plan.
    /// String coerce stays on the host.
    #[pyfunction]
    fn compile_datetime() -> PyPlan {
        compile_datetime_plan()
    }

    /// One-shot DateTime apply. Success is `None` for a
    /// `datetime.datetime`.
    ///
    /// Closed DateTime type door is this extract. A plain
    /// `datetime.date`, raw `str`, `int`, or `bool` raises at this FFI
    /// boundary (extract error); host falls through to the host type
    /// door. No string coerce. No bound unit. Releases the GIL
    /// (`Python::detach`). Compile and apply stay a pair.
    #[pyfunction]
    fn apply_datetime(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: ExtractedDateTime,
    ) -> PyResult<Option<FailKind>> {
        match &plan.body {
            Plan::DateTime => {}
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::Uuid => return Err(unexpected_family("apply_datetime")),
        }
        let _ = value;
        Ok(py.detach(|| None))
    }

    /// Closed Uuid type-door plan. No kwargs. The variant is the
    /// `Uuid` marker. Not a taught L1 API. Not a String plan.
    /// String coerce stays on the host.
    #[pyfunction]
    fn compile_uuid() -> PyPlan {
        compile_uuid_plan()
    }

    /// One-shot Uuid apply. Success is `None` for a `uuid.UUID`,
    /// including the nil UUID.
    ///
    /// Closed Uuid type door is this extract. A Python `str`, `int`,
    /// `bool`, or `bytes` raises at this FFI boundary (extract error);
    /// host falls through to the host type door. No string coerce. No
    /// bound unit. Releases the GIL (`Python::detach`). Compile and
    /// apply stay a pair.
    #[pyfunction]
    fn apply_uuid(
        py: Python<'_>,
        plan: PyRef<'_, PyPlan>,
        value: ExtractedUuid,
    ) -> PyResult<Option<FailKind>> {
        match &plan.body {
            Plan::Uuid => {}
            Plan::Integer(_)
            | Plan::Float(_)
            | Plan::String(_)
            | Plan::Bytes(_)
            | Plan::IntegerEnum(_)
            | Plan::StringEnum(_)
            | Plan::Boolean
            | Plan::Decimal
            | Plan::Date
            | Plan::DateTime => return Err(unexpected_family("apply_uuid")),
        }
        let _ = value;
        Ok(py.detach(|| None))
    }
}
