from guppylang.decorator import guppy
from tests.util import compile_guppy
from guppylang import comptime


def test_basic_type(validate):
    @compile_guppy
    def foo(x: str) -> str:
        return x

    validate(foo)


def test_basic_value(validate):
    @compile_guppy
    def foo() -> str:
        x = "Hello World"
        return x

    validate(foo)


def test_struct(validate):
    @guppy.struct
    class StringStruct:
        x: str

    @guppy
    def main(s: StringStruct) -> None:
        StringStruct("Lorem Ipsum")

    validate(main.compile_function())


def test_string_eq(validate):
    """Test that string equality comparison works."""

    @compile_guppy
    def eq_literals() -> bool:
        """Compare two string literals."""
        return "hello" == "hello"

    @compile_guppy
    def eq_variables() -> bool:
        """Compare two string variables."""
        s1 = "hello"
        s2 = "hello"
        return s1 == s2

    @compile_guppy
    def eq_different() -> bool:
        """Compare two different strings."""
        return "hello" == "world"

    validate(eq_literals)
    validate(eq_variables)
    validate(eq_different)


def test_string_ne(validate):
    """Test that string inequality comparison works."""

    @compile_guppy
    def ne_literals() -> bool:
        """Compare two different string literals with !=."""
        return "hello" != "world"

    @compile_guppy
    def ne_variables() -> bool:
        """Compare two different string variables with !=."""
        s1 = "hello"
        s2 = "world"
        return s1 != s2

    @compile_guppy
    def ne_same() -> bool:
        """Compare two identical strings with !=."""
        return "hello" != "hello"

    validate(ne_literals)
    validate(ne_variables)
    validate(ne_same)


def test_string_eq_comptime(validate):
    """Test that comptime string comparison works (issue #1372)."""

    test_str = "test"

    @compile_guppy
    def eq_comptime() -> bool:
        """Compare a comptime string with a string literal."""
        return comptime(test_str) == "test"

    @compile_guppy
    def eq_comptime_false() -> bool:
        """Compare a comptime string with a different string literal."""
        return comptime(test_str) == "different"

    validate(eq_comptime)
    validate(eq_comptime_false)


def test_string_comparison_in_control_flow(validate):
    """Test that string comparisons work in control flow statements."""

    @compile_guppy
    def in_if_eq() -> int:
        """Use string comparison in an if statement."""
        s = "hello"
        if s == "hello":
            return 1
        else:
            return 0

    @compile_guppy
    def in_if_ne() -> int:
        """Use string inequality in an if statement."""
        s = "hello"
        if s != "world":
            return 1
        else:
            return 0

    validate(in_if_eq)
    validate(in_if_ne)


def test_string_comparison_parameters(validate):
    """Test that string comparisons work with function parameters."""

    @compile_guppy
    def compare_eq(s1: str, s2: str) -> bool:
        """Return the result of string equality comparison."""
        return s1 == s2

    @compile_guppy
    def compare_ne(s1: str, s2: str) -> bool:
        """Return the result of string inequality comparison."""
        return s1 != s2

    validate(compare_eq)
    validate(compare_ne)
