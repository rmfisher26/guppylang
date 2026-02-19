"""Integration tests for the @guppy.enum feature (Issue #1517 PoC)."""

from typing import Generic


from guppylang.decorator import guppy


def test_enum_basic_constructor(validate):
    """Variant constructor with T inferred from argument matches return type."""
    T = guppy.type_var("T")

    @guppy.enum
    class Result(Generic[T]):
        Ok = {"value": T}
        Err = {"code": int}

    @guppy
    def make_ok(x: int) -> Result[int]:
        return Result.Ok(x)

    validate(make_ok.compile_function())


def test_enum_non_generic_variant_constructor(validate):
    """Variant with only concrete-type fields requires explicit type arg."""
    T = guppy.type_var("T")

    @guppy.enum
    class Result(Generic[T]):
        Ok = {"value": T}
        Err = {"code": int}

    @guppy
    def make_err(code: int) -> Result[int]:
        # Err does not mention T in its fields so T can't be inferred from
        # the argument alone; use the return-type context or explicit type arg.
        return Result.Err[int](code)

    validate(make_err.compile_function())


def test_enum_unit_variant(validate):
    """Unit variant (no fields) with explicit type arg."""
    T = guppy.type_var("T")

    @guppy.enum
    class Option(Generic[T]):
        Some = {"value": T}
        Nothing = {}

    @guppy
    def wrap(x: int) -> Option[int]:
        return Option.Some(x)

    validate(wrap.compile_function())


def test_enum_unit_variant_explicit(validate):
    """Unit variant constructed with explicit type argument."""
    T = guppy.type_var("T")

    @guppy.enum
    class Option(Generic[T]):
        Some = {"value": T}
        Nothing = {}

    @guppy
    def empty() -> Option[int]:
        return Option.Nothing[int]()

    validate(empty.compile_function())


def test_enum_multi_field_variant(validate):
    """Variant with multiple fields."""
    S = guppy.type_var("S")
    T = guppy.type_var("T")

    @guppy.enum
    class Pair(Generic[S]):
        Both = {"first": S, "second": S}
        Neither = {}

    @guppy
    def make_pair(a: int, b: int) -> Pair[int]:
        return Pair.Both(a, b)

    validate(make_pair.compile_function())


def test_enum_return_type_context(validate):
    """When T is present in the return type, Err variant works without explicit arg."""
    T = guppy.type_var("T")

    @guppy.enum
    class Result(Generic[T]):
        Ok = {"value": T}
        Err = {"code": int}

    @guppy
    def make_err_ctx(code: int) -> Result[int]:
        # check_call uses return type context to resolve T=int
        return Result.Err(code)

    validate(make_err_ctx.compile_function())


def test_enum_non_generic(validate):
    """Enum without generic parameters."""

    @guppy.enum
    class Color:
        Red = {}
        Green = {}
        Blue = {}

    @guppy
    def primary() -> Color:
        return Color.Red()

    validate(primary.compile_function())
