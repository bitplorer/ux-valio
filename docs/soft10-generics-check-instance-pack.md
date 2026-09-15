# Soft 10 CARTGRAPH — `check_instance` / Generics (evidence pack)

**CARTGRAPH ONLY.** No product tip. No implementation. Soft-patch valio is **read-only**.

Council can ACCEPT Soft LOCK Soft 10 from this pack alone.

---

## Identity

| Item | Value |
| --- | --- |
| Target | [`bitplorer/ux-valio`](https://github.com/bitplorer/ux-valio) `main` |
| `git log -1` HEAD | **`604c9bd7d506bb80ebd75283f94326a1f26c8a12`** |
| Subject | `Soft 9: bag keys are module.qualname on register and lookup (#9)` |
| Soft 9 PR tip SHA | **`453d330f90153aba9e78b07972cf12f376b4e98b`** ([PR #9](https://github.com/bitplorer/ux-valio/pull/9) `headRefOid`) |
| Soft 9 claimed merge | **`604c9bd`** — **verified equal to HEAD** (`mergeCommit` of PR #9) |
| Frozen valio | [`bitplorer/valio@3415c03`](https://github.com/bitplorer/valio/commit/3415c03e37085adda4040671a91eb19aa4fe4ac4) `3415c03e37085adda4040671a91eb19aa4fe4ac4` |
| Valio subject | `Soft 10: compose full validation path; fail-closed units (#10)` — PARKED; not edited |
| Experiment Python | 3.12.3 |
| Package floor | `requires-python = ">=3.10"` (`pyproject.toml` L11) |
| Suite at HEAD | **203 passed** in 0.20s, 20 files (local `python3 -m pytest tests`) |

HEAD check (this run):

```
604c9bd Soft 9: bag keys are module.qualname on register and lookup (#9)
604c9bd7d506bb80ebd75283f94326a1f26c8a12
```

Human ask: **Ensure `check_instance` is robust and stable for Generics too.**

Name honesty: ux-valio has **no** public `check_instance`. The door is module helper `is_instance_of` in `ux_valio/validators/leaves.py`. Valio@3415c03 calls `typingx.isinstancex`. Soft 6 already locks `check_*` free functions out of the public API (`tests/test_product_surface.py` L39–44). Soft 10 hardens that existing helper; it does not mint E14 public algebra.

---

## 1. Tree evidence on ux-valio HEAD `604c9bd`

### 1.1 The type-membership door (one helper, two callers)

`is_instance_of` is the only annotation membership helper. It is **not** in `ux_valio.__all__` and **not** re-exported from `ux_valio.validators`.

```15:49:ux_valio/validators/leaves.py
def is_instance_of(value: Any, annotation: Any) -> bool:
    """Door A type honesty: Union/Optional recurse; other origins use origin.

    ``list[int]`` is a list, not an int. Parametrized args (element types,
    Literal, Annotated) stay permissive on ``isinstance`` TypeError — not
    typingx.
    """
    if annotation is None:
        return True
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        args = get_args(annotation)
        if not args:
            return True
        return any(is_instance_of(value, arg) for arg in args)
    if origin is type(None):
        return value is None
    if origin is None:
        try:
            return isinstance(value, annotation)
        except TypeError:
            return True
    try:
        return isinstance(value, origin)
    except TypeError:
        return True


class TypeValidator(ValidateProperty):
    def _validate_type(self, instance: Any, value: Any) -> None:
        annotation = getattr(self, "annotation", None)
        if annotation is not None and value is not None and not is_instance_of(value, annotation):
            raise TypeError(
                f"{self.name} expect {annotation} type, got {type(value).__name__} type instead"
            )
```

Imports: `typing.Any, Union, get_args, get_origin` plus `types` (`leaves.py` L6–8). **No** `typing_extensions`. **No** `typingx`.

Behavior at HEAD, in one sentence:

- **Union / `Optional` / PEP 604 `|`:** recurse args (works).
- **Any other origin (`list`, `dict`, `tuple`, `Literal`, `Annotated`, `Sequence`, …):** `isinstance(value, origin)` only. **Args are ignored.**
- **`isinstance` `TypeError`:** return **`True`** (fail-**open**). Docstring names this as Soft 1, not typingx.
- **`annotation is None`:** always True.
- **`value is None`:** `_validate_type` skips the helper entirely (`leaves.py` L46). Required owns None. Typed `int` and `Optional[int]` are indistinguishable at the type door for `None`.

### 1.2 Call graph (descriptor vs function-validate)

Same helper. No second type door.

| Path | File:line | What it does |
| --- | --- | --- |
| Descriptor `__set__` → `pre_set` → `validate` | `ux_valio/validators/base.py` L24–28 | Store path. `ValidateProperty.pre_set` is `pre_validation_processing` → `validate` → `post_validation_processing`. |
| Facade path unit `"type"` | `ux_valio/validators/facade.py` L94–97 | `"type": TypeValidator._validate_type` on `DEFAULT_PATH_NAMES` (`path.py` L21–30; `"type"` is second). |
| Typed facades | `ux_valio/validators/facade.py` L121–130; `typed.py` L32–68 | Class `annotation = int` / `str` / `uuid.UUID` / … then inherited `validate()`. |
| Compose root | `ux_valio/validators/compose.py` L180–183 (AllOf), L204–207 (AnyOf) | `TypeValidator._validate_type(self, …)` **before** member `validate()`. |
| Direct `field.validate(instance, value)` | same `_validate_type` | Function-validate. Experiments: **agrees with descriptor** for every Generics case below. |
| `TypeValidator` leaf | `leaves.py` L51–52 | `validate` → `_validate_type`. Same helper. |

`pre_set` hook **is** the validate pipeline. There is still no `add_pre_set` / `_processors["pre_set"]`.

### 1.3 Descriptor `__set_name__` annotation matching (Soft 2 — adjacent, not the type door)

Soft 2 compares **annotations to each other**, not values to annotations. Union forms use stdlib `get_origin` / `get_args`. Container generics are compared by **object identity**, not origin+args.

```26:31:ux_valio/descriptor.py
``__set_name__`` is fail-closed on annotation conflict. If both
``validator.annotation`` and the owner class annotation are set and they
disagree, raise ``TypeError``. Owner wins only when the validator annotation
was ``None``. The validator annotation is kept when the owner has none.
Union forms are compared with stdlib ``get_origin`` / ``get_args``
(``typing.Union`` and ``X | Y``), not typingx / typing_extensions.
```

```40:51:ux_valio/descriptor.py
def _annotation_identity(annotation: Any) -> Any:
    """Hashable identity for stdlib union forms. ``Union[X, Y]`` and ``X | Y`` agree."""
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        return (Union, frozenset(_annotation_identity(arg) for arg in get_args(annotation)))
    return annotation


def _annotations_agree(left: Any, right: Any) -> bool:
    if left is right:
        return True
    return _annotation_identity(left) == _annotation_identity(right)
```

```135:165:ux_valio/descriptor.py
    def __set_name__(self, owner: type, name: str) -> None:
        # valio@3415c03 valio/descriptor/descriptors.py L134–202:
        # _set_name + _may_set_or_ensure_annotation_match. Fail closed; not debug-swallow.
        ...
            self._bind_owner_annotation(owner, name)
        except Exception as err:
            self.errors.append(err)
            raise

    def _bind_owner_annotation(self, owner: type, name: str) -> None:
        annotations = getattr(owner, "__annotations__", None) or {}
        owner_annotation = annotations.get(name)
        if self.annotation is None:
            if owner_annotation is not None:
                self.annotation = owner_annotation
            return
        if owner_annotation is None:
            return
        if not _annotations_agree(self.annotation, owner_annotation):
            raise TypeError(...)
```

Compose reuses the same identity (`compose.py` L13, L89–103, L119–125). Conflicting typed facades fail at compose (`tests/test_validator_compose.py` L135–137).

### 1.4 Other `isinstance` sites (not annotation matching)

These are **not** the Generics door. Listed so Council does not confuse them with `is_instance_of`.

| File:line | Role |
| --- | --- |
| `descriptor.py` L55, L72–88, L127 | kwarg type checks; string annotation **label**; `ValidationErrors` unwrap |
| `pattern.py` L23–47 | `PatternType` combinators |
| `errors.py` L32 | `ValidationErrors` unwrap |
| `base.py` L74, L81 | `&` / `|` require `ValidateProperty` |
| `compose.py` L25, L217 | compose parts; error unwrap |
| `hooks.py` L53 | `namespace=` must be `str` |
| `facade.py` L59–63 | `required` / `reassign` bool |
| `leaves.py` L57, L81–86, L95 | required/reassign bool; pattern text |
| `typed.py` L59, L71, L79, L87, L138–160 | UUID/Path coerce; Enum membership (separate from field annotation) |
| `expiry.py` L16–56 | date-ish parse |
| `payment.py` L43 | card number must be `str` |

Enum facades (`typed.py` L131–163) leave class `annotation` unset so a concrete enum may own the field, then `isinstance(value, enum.Enum)` in `validate()`. That is a named extra check, not Generics.

### 1.5 Tests that already lock origin-only Generics

`tests/test_door_a_honesty.py` L45–92:

- `list[int]` accepts `[1, 2]`, rejects `1` (origin).
- `dict[str, int]` accepts `{"a": 1}`, rejects `"a"` (origin).
- `list[int] | None` accepts list and `None`, rejects `1`.
- `int | str` rejects `float`.

**No test** asserts element types, nested generics, `tuple[int, ...]`, `typing.List` vs `list`, `TypeVar`, `Protocol`, `TypedDict`, `NewType`, `Literal`, or `Annotated`.

Soft 2 union identity: `tests/test_annotation_conflict.py` L110–137 (`Optional[int]` agrees with `int | None`; `Union[int, str]` agrees with `int | str`). L96–107: `int | None` and `int | str` **conflict** with `IntegerValidator` (`annotation = int`). L147–163: postponed `from __future__ import annotations` makes the owner annotation the **string** `'int'`, which conflicts with live `int` on `IntegerValidator`.

### 1.6 Generics matrix (local experiments, not committed)

Helper: `is_instance_of` plus Door A `__set__` and `Validator.validate()`. Descriptor and function-validate **agreed on every row.**

Legend: **WORK** = accepts good / rejects bad. **FAIL_SILENT** = accepts a value that violates the annotation args. **RAISE_WRONG** = TypeError on a value that matches the annotation. **FAIL_OPEN** = unknown form treated as valid for any value (`TypeError` → `True`).

| Case | `get_origin` / `get_args` | HEAD result | Bucket |
| --- | --- | --- | --- |
| `list[int]` + `[1, 2]` | `list`, `(int,)` | accept | WORK (origin) |
| `list[int]` + `["a"]` | same | accept | **FAIL_SILENT** (elements) |
| `list[int]` + `1` | same | TypeError | WORK |
| `list[int]` + `(1,)` | same | TypeError | WORK |
| `list[int]` + `[]` | same | accept | WORK-origin (empty; args unused) |
| `typing.List[int]` + `[1, 2]` / `["a"]` | `list`, `(int,)` | same as `list[int]` | WORK origin / **FAIL_SILENT** elems |
| `dict[str, int]` + `{"a": 1}` | `dict`, `(str, int)` | accept | WORK (origin) |
| `dict[str, int]` + `{1: "a"}` | same | accept | **FAIL_SILENT** (key/val) |
| `dict[str, int]` + `"a"` | same | TypeError | WORK |
| `Optional[int]` / `int \| None` + `1` / `None` / `"x"` | `Union` / `UnionType` | accept / accept / reject | **WORK** |
| `Union[int, str]` / `int \| str` + `1.5` | Union | reject | **WORK** |
| `list[int] \| None` + `["a"]` | Union of list | accept | **FAIL_SILENT** (elems) |
| `list[list[int]]` + `[[1]]` | `list`, `(list[int],)` | accept | WORK-origin |
| `list[list[int]]` + `[[1, "a"]]` | same | accept | **FAIL_SILENT** nested elems |
| `list[list[int]]` + `[1]` | same | accept | **FAIL_SILENT** inner not list |
| `tuple[int, ...]` + `(1, 2)` | `tuple`, `(int, Ellipsis)` | accept | WORK-origin |
| `tuple[int, ...]` + `("a",)` | same | accept | **FAIL_SILENT** elems |
| `tuple[int, ...]` + `[1, 2]` | same | TypeError | WORK |
| `tuple[int, str]` + `(1,)` / `(1, 2, 3)` | `tuple`, `(int, str)` | accept | **FAIL_SILENT** arity |
| `set[int]` + `{1}` / `{"a"}` | `set` | accept / accept | WORK origin / **FAIL_SILENT** |
| `Mapping[str, int]` + `{1: "a"}` | `collections.abc.Mapping` | accept | **FAIL_SILENT** |
| `Sequence[int]` + `[1]` / `1` | `Sequence` | accept / reject | WORK origin; elems unchecked |
| `Callable[[int], str]` + `len` / `1` | `Callable` | accept / reject | WORK origin; **signature unchecked** |
| `TypeVar("T")` + any value | `None` | accept | **FAIL_OPEN** (`isinstance` TypeError → True) |
| `TypeVar(bound=int)` + `"a"` | `None` | accept | **FAIL_OPEN** (bound ignored) |
| `NewType("UserId", int)` + `1` / `"a"` | `None` | accept / accept | **FAIL_OPEN** / **FAIL_SILENT** (no unwrap) |
| `Literal["a"]` + `"a"` / `"b"` / `1` | `Literal` | accept all | **FAIL_OPEN** / **FAIL_SILENT** |
| `@runtime_checkable` Protocol + Duck / `1` | `None` | accept / reject | **WORK** (plain `isinstance`) |
| Protocol **without** runtime_checkable | `None` | accept Duck | **FAIL_OPEN** (TypeError → True) |
| `TypedDict` Movie + `{}` / complete dict | `None` | accept both | **FAIL_OPEN** (`TypedDict` forbids isinstance) |
| `typing.Any` + anything | `None` | accept | FAIL_OPEN form, but **Any is correct** |
| `Annotated[int, "meta"]` + `1` | `Annotated` | **TypeError** | **RAISE_WRONG** (`isinstance(1, Annotated)` is False, not TypeError) |
| `ClassVar[int]` / `Final[int]` + `"x"` | ClassVar / Final | accept | **FAIL_OPEN** |
| User `class Box(Generic[T])` + `Box[int]` | origin is `Box` | `Box("a")` accepted | **FAIL_SILENT** (param unused) |
| `from __future__ import annotations` + `items: list[int]` | annotation is **`str`** `"list[int]"` | `Box(items=1)` **stores 1** | **FAIL_OPEN** (string → TypeError → True) |
| `IntegerValidator` on `list[int]` field | Soft 2 | TypeError at class body | WORK (typed facade vs container) |
| `Validator.annotation = List[int]` vs owner `list[int]` | Soft 2 identity | TypeError at class body | **RAISE_WRONG** / surprising (same meaning, different objects) |
| `None` assigned to `IntegerValidator` via `validate()` | skip at L46 | pass | KEEP (Required owns None) |
| `bool` as `int` | `isinstance(True, int)` | accept | KEEP (`tests/test_descriptor_lifecycle.py` L64–78) |

Builtin `isinstance([1], list[int])` raises `TypeError: parameterized generic` on 3.12. HEAD never calls that; it uses origin. Good. The hole is **not using args after origin**.

Soft 2 identity experiment (`_annotations_agree`):

| Pair | Agree? |
| --- | --- |
| `Optional[int]` vs `int \| None` | True (union identity) |
| `Union[int, str]` vs `int \| str` | True |
| `list[int] \| None` vs `Optional[list[int]]` | True |
| `list[int]` vs `typing.List[int]` | **False** |
| `dict[str, int]` vs `typing.Dict[str, int]` | **False** |
| `tuple[int, ...]` vs `typing.Tuple[int, ...]` | **False** |
| `list[int]` vs `list[str]` | False |
| `list[int]` vs `list` | False |

### 1.7 Suite counts (HEAD, no product change)

```
203 passed in 0.20s
203 tests collected, 20 files
```

| File | Count | Generics relevance |
| --- | --- | --- |
| `tests/test_annotation_conflict.py` | 15 | Soft 2 bind; Union/Optional identity; postponed string label |
| `tests/test_door_a_honesty.py` | 12 | origin-only `list[int]` / `dict[str,int]` / unions; no element tests |
| `tests/test_descriptor_lifecycle.py` | 10 | `TypeValidator` / `IntegerValidator`; bool-as-int |
| `tests/test_validator_compose.py` | 10 | compose annotation conflict |
| `tests/test_product_surface.py` | 8 | `check_*` not public; **`docs/soft*.md` forbidden** (L89–91) |
| remaining 15 files | 148 | not the type-membership door |

This pack file lives at `docs/soft10-generics-check-instance-pack.md` so Council can read it on the branch. Soft 6 `test_no_process_pack_docs_in_tree` will fail if this file is on `main`. That test is KEEP. **Do not merge this pack into product `main` as a ceremony strip regression.** ACCEPT the LOCK from the pack; delete or leave unmerged after Council.

---

## 2. valio @ `3415c03` read-only

Checked out `3415c03e37085adda4040671a91eb19aa4fe4ac4`. Not edited.

### 2.1 `isinstancex` is the type door

```65:65:valio/validator/validators.py
from typingx import isinstancex
```

```403:412:valio/validator/validators.py
    def _validate_type(self, instance, value):  # noqa
        if logger := self.logger:
            logger.info(f"{self.name}: Type: {self.annotation}")
        
        if self.annotation is not None:
            if value is not None and not isinstancex(value, self.annotation):
                raise TypeError(
                    f"{self.name} expect {self.annotation} type, "
                    f"got {type(value).__name__} type instead"
                )
```

Same None-skip as ux-valio. The difference is **`isinstancex` walks Generics args**.

`typingx==0.6.0` (valio `pyproject.toml` L9; `poetry.lock` typingx 0.6.0) — PrettyWood/typingx:

- `isinstancex` / `issubclassx` wrap `_isinstancex` / `_issubclassx` and on `AttributeError`/`TypeError` return **`False`** (fail-**closed**). Opposite of ux-valio `True`.
- Recurses `Union` / PEP 604, `list`/`List` (elements, empty list True), `dict`/`Dict` (keys and values), `set`, `tuple`/`Tuple` including `T, ...` and fixed arity, `Sequence`, `Mapping`, `Collection`, `Literal`, `NewType` unwrap, `Annotated` strip + optional `Constraints`, `TypedDict` required keys, `Callable` signatures.
- Uses **its own** `get_origin` / `get_args` in `typingx/typing_compat.py` so 3.6–3.10 behave like 3.10. On Python ≥ 3.9 that is stdlib `typing.get_origin` / `get_args`.
- Extra algebra ux-valio must **not** import: `Constraints`, `Listx`/`Tuplex`, dict-literal TypedDict shortcuts, `func_check`.

Valio never names `check_instance`. The human phrase maps to `isinstancex(value, self.annotation)` here and `is_instance_of` on ux-valio.

### 2.2 `issubclassx` is the Soft 2 bind door

```13:13:valio/descriptor/descriptors.py
from typingx import issubclassx
```

```174:191:valio/descriptor/descriptors.py
                    if not issubclassx(owner_annotation, self_annotation):
                        ...
                        raise TypeError(
                            f"{owner.__name__}.{self.name}: {owner_annotation_name}"
                            f" annotation did not match {type(self).__qualname__}: "
                            f"{self_annotation_name}"
                        )
                    if owner_annotation != self.annotation:
                        self.annotation = owner_annotation
```

Called from `__set_name__` L232 + L250. typingx `issubclassx` is documented **WIP**. Valio needed it because facades store **dual-schema** aliases:

```322:355:valio/validator/validators.py
V = typing.TypeVar("V", bound=ValidateProperty)
T = typing.TypeVar("T")
Union = typing.Union[T, V, None]
INT = Union[int, V]
LIST = Union[list, V]
DICT = Union[dict, V]
...
```

`IntegerValidator.annotation = INT` (`L1976`). Owner `int` is a subclass-x of `Union[int, Validator, None]`. Soft 2 on ux-valio **retired** that: facades store plain `int` / `str` / `bool` (`facade.py` L121–130). Dual-schema `Union[T, Validator]` remains **HOLD**.

### 2.3 `typing_extensions` is not the type door

| Site | Use |
| --- | --- |
| `valio/logger/color_format.py` L16 | `from typing_extensions import Final, Literal` — logger formatting only |
| `poetry.lock` `typing-extensions` 4.5.0 | pulled for old-Python typingx; valio floor is `python = "^3.10"` |
| typingx on 3.10+ | stdlib `typing.Annotated` / `Literal` / `get_origin`; `typing_extensions` only if `python < 3.9.2` |

**No** `typing_extensions` on the isinstance/issubclass path. Soft 2 already preferred stdlib `get_origin` / `get_args` for union identity. Soft 10 keeps that preference for membership too.

### 2.4 Valio Generics locks that exist vs parked

| Lock | Where | vs ux-valio HEAD |
| --- | --- | --- |
| Element-aware `list[T]` / `dict[K,V]` / nested | `isinstancex` | **GAP** — origin-only |
| `tuple[T, ...]` arity/elems | `isinstancex` `_is_valid_sequence` | **GAP** |
| Fail-closed unknown (`TypeError` → False) | `isinstancex` L80–83 | **GAP** — ux-valio → True |
| Dual-schema `INT = Union[int, V]` | `validators.py` L329+ | **HOLD / RETIRE** on Door A (plain `int`) |
| `ListValidator` / `DictionaryValidator` / `Set` / `Tuple` | `validators.py` L2424–2445 `annotation = LIST` (`Union[list, V]`) | **DEFER** collections facades (README already: “Phone, list/dict/set/tuple collection facades are not shipped”) |
| Commented Generic experiment | `validators.py` L2490–2492 `issubclassx(cls, typing.Generic)` | parked scratch; not a product lock |
| Commented nested `dict[str, list[set[int]]]` | L2484 | shows **intent** that `isinstancex` walk nested containers; owner annotation is dual-schema Union |
| `from __future__ import annotations` banned | `validators.py` L8–10 | valio minced by postponed strings. ux-valio uses future annotations in product modules; owner postponed strings are a live hole (matrix above) |

### 2.5 KEEP / RETIRE / GAP vs Soft 2 stdlib `get_origin` / `get_args`

| | |
| --- | --- |
| **KEEP** | Stdlib `typing.get_origin` / `get_args` for Union **and** (Soft 10) for container origin+args. Python ≥ 3.10 floor. No `typingx`. No `typing_extensions` on this door. Union/Optional/PEP 604 recurse already on HEAD. Origin check so `list[int]` is a list, not an int (`test_door_a_honesty.py` L45–55). None-skip on `_validate_type`. bool-as-int. One helper for descriptor and `validate()`. `check_*` not public. |
| **RETIRE** | typingx `isinstancex` / `issubclassx` as a dependency. typingx `Constraints` / `Listx` / Callable-signature checker / dict-as-TypedDict. Dual-schema `Union[T, Validator]` as the reason to call `issubclassx`. Soft 1 **TypeError → True** permissiveness for parametrized args (named in `is_instance_of` docstring L18–20). |
| **GAP** | Recurse container args. Fail-closed unknown annotations. `Annotated` strip (HEAD **RAISE_WRONG**). `NewType` unwrap. `Literal` membership. Postponed string annotations fail-closed. Optional: origin+args **identity** so `list[int]` agrees with `List[int]` (Soft 2 currently identity-only for non-unions). |

---

## 3. Soft LOCK Soft 10 proposal

Harden the existing check door. **No** new public `check_instance` / `check_type` / typing module. **No** Cap / Soft ceremony in product code. **No** `add_pre_set`.

Soft 1 docstring said parametrized args stay permissive. Soft 10 **retires that permissiveness** for interpreted generics. Council ACCEPT is a lock change, not a silent reread of Soft 1.

### DO

1. **Harden `is_instance_of(value, annotation)` in place.** Same helper for `__set__` and `validate()`. Do not export it. Do not rename it onto `__all__`.
2. **Recurse origin+args** with stdlib `get_origin` / `get_args` only:
   - `list` / `typing.List` — every element.
   - `tuple` / `typing.Tuple` — `tuple[T, ...]` (all elems `T`); `tuple[A, B, …]` fixed arity (length + per-index).
   - `dict` / `typing.Dict` — every key **and** value.
   - `set` / `frozenset`.
   - Nested (`list[list[int]]`, `dict[str, list[int]]`) by calling the same helper.
   - `collections.abc.Sequence` / `Mapping` / `Set` / `Collection` / `Mutable*` **when they appear as annotations** (membership recurse). This is not shipping `ListValidator` facades.
3. **Empty containers accept** (no elements to disprove). Aligns with typingx empty-list True.
4. **Fail-fast inside the walk.** First bad element → `False` → `TypeError`. Do not collect element failures. `collect_all` stays a concern-path flag (Soft 7), not an element walker.
5. **Fail-closed unknown:** if the annotation cannot be interpreted with the rules below, return **`False`**, not `True`. `isinstance` `TypeError` is not “valid”.
6. **Interpret with stdlib, still not typingx:**
   - `typing.Any` → True.
   - `annotation is None` → True (unset).
   - `Union` / `types.UnionType` / `Optional` → any-of recurse (already).
   - `Annotated[T, …]` → strip to `T` then recurse (**fixes RAISE_WRONG** on HEAD).
   - `NewType` → unwrap `__supertype__` until a real type.
   - `Literal[...]` → value in `get_args`.
   - `TypeVar`: if bound, check bound; if constraints, treat as Union of constraints; else False.
   - `@runtime_checkable` Protocol → `isinstance`; non-runtime Protocol → False.
   - Postponed **string** annotations → False (no `eval`).
7. **Tests** (tips Soft, not this pack): every matrix row that is FAIL_SILENT or RAISE_WRONG today; descriptor **and** `validate()`; `list` vs `List`; nested; `tuple[int, ...]`; postponed string.

### KEEP

- Soft 1 Door A `field: T = SomeValidator(...)`. Debug-swallow. Logger OFF. Falsy `0` / `False` / `""`. Pattern `findall`.
- Soft 2 fail-closed annotation **conflict**; owner wins only when validator annotation was None; name mismatch `AttributeError`; stdlib union identity; no write-back onto `owner.__annotations__`.
- Soft 3 honesty harden.
- Soft 5 async `add_*`; no `asyncio.run` in `__set__`; nest-safe worker bridge.
- Soft 7 compose-root hooks; dual-door honesty; opt-in `collect_all`; path fail-closed.
- Soft 8 PaymentCard ∩ Luhn; Expiry exclusive bounds; named-once on those leaves.
- Soft 9 bag keys `module.qualname`.
- Soft-patch valio **PARKED** @ `3415c03`. Do not edit valio.
- `value is None` skips the type door. Required owns None.
- `isinstance(True, int)` is True (bool-as-int).
- Union/Optional/PEP 604 recurse.
- Origin so `list[int]` rejects a bare `int`.
- Facades do not multiple-inherit concern leaves. `Chain` is `AllOf`.
- No Cap Host, `mount_channel`, Field twin, Schema twin, `rule/`, Result, RGB/HSL, star-import barrel.
- `check_*` free functions are not public API.

### DEAD

- `typingx` as a product dependency.
- `typing_extensions` on the type-membership door.
- Public `check_instance` / `check_type` / E14 typing algebra package.
- typingx `Constraints`, `Listx`/`Tuplex`, Callable **signature** checking, dict-literal TypedDict shortcuts, `func_check`.
- `eval` / `get_type_hints` as a silent door to resolve postponed strings inside `is_instance_of`.
- Porting valio dual-schema `INT = Union[int, Validator, None]` so `issubclassx` becomes necessary.

### DO NOT

- Phone / `ListValidator` / `DictionaryValidator` / `SetValidator` / `TupleValidator` collection **facades** — **DEFER** (README already).
- Dual-schema / typingx / pyparsing — **HOLD**.
- Compose reopen (“compose #30 park”). Valio Soft 10 already composed the path; ux-valio Soft 7 already hung hooks on the compose root. Soft 10 here is **membership**, not another compose Soft.
- User `Generic[T]` instance-field inspection (`__orig_class__` etc.) — origin `isinstance` only; do not invent a runtime Generic inspector.
- TypedDict **key schema** — **HOLD** with collections DEFER. Fail-closed (`False`) so `{}` is not silently a `Movie`. Do not ship a TypedDict validator facade.
- Changing Soft 2 to valio `issubclassx` (subclass / dual-schema).
- Product Soft ceremony tokens in `ux_valio/` / README / AGENTS / CHANGELOG.
- `add_pre_set` / `_processors["pre_set"]`.
- Raising the Python floor above 3.10, or dropping 3.10 (`list[T]` and `X | Y` are native).

### Coupled Soft 2 DO (stdlib identity, still not typingx)

`_annotation_identity` already special-cases Union so `Union[X, Y]` and `X | Y` agree. **Extend the same idea** to `list`/`dict`/`tuple`/`set`/`frozenset` origin+args so `list[int]` agrees with `typing.List[int]`. Nested. Recurse args through Union.

Without this, `field.annotation = List[int]` vs owner `list[int]` is a class-body `TypeError` (measured). That is the Soft 2 × Soft 10 interaction. It is still stdlib. It is **not** `issubclassx`.

Do **not** make `int` agree with `list[int]`. Do **not** make `list` agree with `list[int]` (bare vs parametrized stay a conflict).

### Fail-closed policy (LOCK sentence)

**If `is_instance_of` cannot interpret `annotation` with stdlib origin/args plus the explicit forms in DO.6, return False.** Never return True because `isinstance` raised `TypeError`. `Any` and unset `None` annotation are the only “accept anything” forms.

### Origin+args recursive vs `typing_extensions`

Use **stdlib** `typing.get_origin` / `typing.get_args` (3.10+). Recurse. Do not vendor typingx’s `typing_compat` shims. Do not import `typing_extensions` to read `Literal` / `Annotated` / `get_origin` — they are in `typing` on the package floor.

---

## 4. Risks

### 4.1 Soft 2 annotation conflict

- **PEP 585 vs `typing.List`:** identity mismatch today; coupled DO above.
- **Postponed annotations:** product modules use `from __future__ import annotations`. Owner `__annotations__` may be strings. Soft 2 already fail-closes `IntegerValidator` (`int`) vs `'int'`. Bare `Validator()` **copies** the string and then type-checks fail-open (`Box(items=1)` stores `1`). Soft 10 fail-closed strings close that hole; they do not resolve the string. Callers who need live generics must not postpone, or must assign a live annotation on the validator. Do not `eval`.
- **`IntegerValidator` on `list[int]`:** TypeError at class body. **KEEP.** Element checks do not belong on `annotation = int`.

### 4.2 Descriptor vs function-validate

Measured: they already share `_validate_type` and agree. Soft 10 must keep one helper. A second implementation on `validate()` only would be a dual door (forbidden). Compose roots already call the same `_validate_type` before members.

### 4.3 Deep Generics performance

Origin-only is O(1). Recurse is O(n) / nested. A million-int `list[int]` walks a million times. LOCK: fail-fast; no element-level `collect_all`; no caching door (`cache_task` kwarg KEEP, cache behavior RETIRE — do not revive a type-check cache). Pathological nesting is a caller problem; do not add a depth cap unless a later Soft measures one.

### 4.4 Package Python floor

`requires-python = ">=3.10"` with classifiers 3.10–3.12. PEP 585 and PEP 604 are native. Soft 10 must run on 3.10 (stdlib `types.UnionType` exists). Do not add `typing_extensions` “for 3.10 Literal” — `typing.Literal` is 3.8+. Do not lower the floor. Do not raise it to 3.11/3.12 for `typing.TypeAliasType` or PEP 695 `type` statements — those stay unknown → fail-closed until a later Soft.

---

## ACCEPT text (Council)

**Soft LOCK Soft 10:** Harden existing `is_instance_of` (unexported) with stdlib `get_origin`/`get_args` origin+args recurse for list/dict/tuple/set/frozenset and abc Sequence/Mapping/Set/Collection; Union/Optional already. Fail-closed unknown (`TypeError` → False), except `Any` and unset annotation. Strip `Annotated`, unwrap `NewType`, `Literal` membership, TypeVar bound/constraints else False, runtime_checkable Protocol via `isinstance` else False, postponed strings False, TypedDict False (schema HOLD). Empty containers True. Fail-fast element walk. Extend Soft 2 identity to container origin+args so `list[int]` agrees with `List[int]`. No typingx, no typing_extensions, no public `check_instance`, no collection facades, no dual-schema, no compose reopen, no Cap/`add_pre_set`. KEEP Soft 1/3/5/7/8/9, valio PARKED @ 3415c03, None-skip, bool-as-int, Python ≥ 3.10.

Tips Soft (after ACCEPT) implements that helper + tests. This pack is not that tip.

---

## Evidence index

| Claim | Cite |
| --- | --- |
| HEAD SHA | `git log -1` → `604c9bd7d506bb80ebd75283f94326a1f26c8a12` |
| Soft 9 tip vs merge | GitHub PR #9 `headRefOid` `453d330…`, `mergeCommit` `604c9bd…` |
| Type door | `ux_valio/validators/leaves.py` L15–49 |
| Descriptor bind | `ux_valio/descriptor.py` L40–51, L135–165 |
| Compose type + identity | `ux_valio/validators/compose.py` L89–103, L180–183, L204–207 |
| Facade `"type"` unit | `ux_valio/validators/facade.py` L94–97 |
| `check_*` not public | `tests/test_product_surface.py` L39–44; `validators/__init__.py` L3–4 |
| Origin-only tests | `tests/test_door_a_honesty.py` L45–92 |
| Valio `isinstancex` | `valio/validator/validators.py` L65, L403–412 @ `3415c03` |
| Valio `issubclassx` | `valio/descriptor/descriptors.py` L13, L174–191, L232–250 |
| Valio dual-schema | `valio/validator/validators.py` L322–355, L1976 |
| Valio collections facades | `valio/validator/validators.py` L2424–2445 |
| typingx fail-closed + recurse | typingx 0.6.0 `main.py` L79–227, L268–312 |
| `typing_extensions` only in valio logger | `valio/logger/color_format.py` L16 |
| Python floor | ux-valio `pyproject.toml` L11; valio `python = "^3.10"` |
| Suite | 203 passed, 20 files, Python 3.12.3 |
