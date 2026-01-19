"""
Comprehensive unit tests for ArrayIndexChecker class.
Tests cover all edge cases, both valid and invalid scenarios.
"""

import pytest
from guppylang import guppy
from guppylang.std.builtins import array
from guppylang_internals.error import GuppyError
from guppylang.std.quantum import qubit, measure, h, discard_array


def test_positive_index_equals_array_size():
    @guppy
    def main() -> int:
        arr = array(i for i in range(5))
        return arr[5]  # Index 5 is invalid for size 5 (valid: 0-4)

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 5
    assert err.size == 5


def test_positive_index_one_past_array_size():
    @guppy
    def main() -> int:
        arr = array(i for i in range(5))
        return arr[6]

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 6
    assert err.size == 5


def test_positive_index_far_beyond_array_size():
    @guppy
    def main() -> int:
        arr = array(i for i in range(10))
        return arr[100]

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 100
    assert err.size == 10


def test_positive_large_array_out_of_bounds():
    @guppy
    def main() -> int:
        arr = array(i for i in range(1000))
        return arr[1000]  # Valid indices: 0-999

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 1000
    assert err.size == 1000


def test_negative_index_minus_one():
    @guppy
    def main() -> int:
        arr = array(i for i in range(5))
        return arr[-1]

    reg_expr = r"Array index -1 is out of bounds"
    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -1
    assert err.size == 5


def test_negative_index_large():
    @guppy
    def main() -> int:
        arr = array(i for i in range(5))
        return arr[-100]

    reg_expr = r"Array index -100 is out of bounds"
    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -100
    assert err.size == 5


def test_valid_index_zero():
    @guppy
    def main() -> int:
        arr = array(42 for _ in range(5))
        return arr[0]

    main.compile()  # Should succeed


def test_valid_index_last():
    @guppy
    def main() -> int:
        arr = array(i * 2 for i in range(10))
        return arr[9]  # Last valid index for size 10

    main.compile()  # Should succeed


def test_valid_index_middle():
    @guppy
    def main() -> int:
        arr = array(i for i in range(100))
        return arr[50]

    main.compile()  # Should succeed


def test_valid_multiple_indexes():
    @guppy
    def main() -> int:
        arr = array(i for i in range(10))
        x = arr[0]
        y = arr[5]
        z = arr[9]
        return x + y + z

    main.compile()  # Should succeed


def test_setitem_positive_index():
    @guppy
    def main() -> None:
        arr = array(0 for _ in range(5))
        arr[10] = 42

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 10
    assert err.size == 5


def test_setitem_negative_index():
    @guppy
    def main() -> None:
        arr = array(0 for _ in range(5))
        arr[-1] = 42

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -1
    assert err.size == 5


def test_setitem_valid_index():
    @guppy
    def main() -> None:
        arr = array(0 for _ in range(5))
        arr[0] = 42
        arr[4] = 99

    main.compile()  # Should succeed


def test_runtime_index_in_helper():
    @guppy
    def get_value(arr: array[int, 10], idx: int) -> int:
        return arr[idx]  # Runtime index

    @guppy
    def main() -> int:
        arr = array(i * 2 for i in range(10))
        return get_value(arr, 5)

    main.compile()  # Should succeed


def test_valid_computed_variable_index():
    @guppy
    def main() -> int:
        arr = array(i for i in range(10))
        x = 5
        return arr[x]  # x is assigned, not a literal - no static check

    main.compile()  # Should succeed


def test_invalid_computed_variable_index():
    @guppy
    def main() -> int:
        arr = array(i for i in range(10))
        x = 50
        return arr[x]  # x is assigned, not a literal - no static check

    main.compile()  # Should succeed


def test_nested_array_valid():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[1][2]  # Outer array has size 5

    main.compile()  # Should succeed


def test_nested_array_outer_oob():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[5][0]  # Outer array has size 5

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 5
    assert err.size == 5


def test_nested_array_inner_oob():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[0][10]  # Inner array has size 10

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 10
    assert err.size == 10


def test_nested_array_inner_negative_oob():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[0][-10]  # Inner array has size 10

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -10
    assert err.size == 10


def test_nested_array_outer_negative_oob():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[-5][0]  # Inner array has size 10

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -5
    assert err.size == 5


def test_nested_array_outer_and_inner_positive_oob():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[5][10]  # Outer array h as size 5, Inner array has size 10

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 5  # the error is only catching at outer array, and fails first
    assert err.size == 5


def test_nested_array_outer_and_inner_negative_oob():
    @guppy
    def main() -> int:
        matrix = array(array(i + j for i in range(10)) for j in range(5))
        return matrix[-5][-10]  # Outer array h as size 5, Inner array has size 10

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -5  # the error is only catching at outer array, and fails first
    assert err.size == 5


def test_index_zero_on_large_array():
    @guppy
    def main() -> int:
        arr = array(i for i in range(1000))
        return arr[0]

    main.compile()  # Should succeed


def test_first_error_caught():
    @guppy
    def main() -> int:
        arr = array(i for i in range(10))
        x = arr[10]  # First error - should be caught here
        y = arr[20]  # Second error - won't reach this
        return x + y

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 10
    assert err.size == 10


def test_check_mode_return_statement():
    @guppy
    def main() -> int:
        arr = array(i for i in range(5))
        return arr[5]  # Check mode: expected type is int

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 5
    assert err.size == 5


def test_synthesize_mode_assignment():
    @guppy
    def main() -> None:
        arr = array(i for i in range(5))
        x = arr[5]  # Synthesize mode: infer type of x

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 5
    assert err.size == 5


def test_method_is_borrowed_valid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        result = qs.is_borrowed(3)  # Valid index
        discard_array(qs)

    main.compile()  # Should succeed


def test_method_is_borrowed_invalid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        result = qs.is_borrowed(12)  # Invalid index
        discard_array(qs)

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 12
    assert err.size == 10


def test_method_take_valid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        q = qs.take(5)  # inbounds, take qubit out of array
        measure(q)
        discard_array(qs)

    main.compile()


def test_method_take_invalid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        q = qs.take(-10)  # Out of bounds
        measure(q)
        discard_array(qs)

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -10
    assert err.size == 10


def test_method_put_valid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        qs.put(qubit(), 0)  # Put a fresh qubit back into the array
        discard_array(qs)

    main.compile()  # Should succeed


def test_method_take_put_valid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        measure(qs.take(3))  # Take it out to make space for the new one
        qs.put(qubit(), 3)
        h(qs[3])
        discard_array(qs)

    main.compile()  # Should succeed


def test_method_take_put_invalid_index():
    @guppy
    def main() -> None:
        qs = array(qubit() for _ in range(10))
        measure(qs.take(3))  # Take it out to make space for the new one
        qs.put(qubit(), -3)
        h(qs[-3])
        discard_array(qs)

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == -3
    assert err.size == 10


def test_boundary_size_2_index_0():
    @guppy
    def main() -> int:
        arr = array(i for i in range(2))
        return arr[0]

    main.compile()  # Should succeed


def test_boundary_size_2_index_1():
    @guppy
    def main() -> int:
        arr = array(i for i in range(2))
        return arr[1]

    main.compile()  # Should succeed


def test_boundary_size_2_index_2():
    @guppy
    def main() -> int:
        arr = array(i for i in range(2))
        return arr[2]

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 2
    assert err.size == 2


def test_in_loop_context():
    @guppy
    def main() -> int:
        arr = array(i for i in range(10))
        total = 0
        for i in range(5):
            total += arr[10]  # Constant out of bounds
        return total

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 10
    assert err.size == 10


def test_in_conditional():
    @guppy
    def main(flag: bool) -> int:
        arr = array(i for i in range(10))
        if flag:
            return arr[10]  # Out of bounds
        else:
            return arr[0]

    with pytest.raises(GuppyError) as excinfo:
        main.compile()

    err = excinfo.value.error
    assert err.title == "Index out of bounds"
    assert err.index == 10
    assert err.size == 10
