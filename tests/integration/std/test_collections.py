from guppylang import guppy
from guppylang.std.collections import (
    Stack,
    empty_stack,
    PriorityQueue,
    empty_priority_queue,
    Queue,
    empty_queue,
)
import pytest
from guppylang.emulator import EmulatorError


def test_stack(run_int_fn) -> None:
    @guppy
    def main() -> int:
        stack: Stack[int, 10] = empty_stack()
        for i in range(10):
            stack = stack.push(i)
        s = 0
        i = 1
        while len(stack) > 0:
            x, stack = stack.pop()
            s += x * i
            i += 1
        stack.discard_empty()
        return s

    run_int_fn(
        main,
        # multiplier * value for ordered values in the stack
        sum((i + 1) * x for i, x in enumerate(reversed(list(range(10))))),
    )


def test_stack_iter(run_int_fn) -> None:
    @guppy
    def main() -> int:
        stack: Stack[int, 10] = empty_stack()
        for i in range(10):
            stack = stack.push(i)
        s = 0
        i = 1
        for x in stack:
            s += x * i
            i += 1
        return s

    run_int_fn(
        main,
        # multiplier * value for ordered values in the stack
        sum((i + 1) * x for i, x in enumerate(reversed(list(range(10))))),
    )


def test_priority_queue(run_int_fn) -> None:
    @guppy
    def main() -> int:
        pq: PriorityQueue[int, 10] = empty_priority_queue()
        for i in range(10):
            # values are in order, priority is reversed
            pq = pq.push(i, 9 - i)
        s = 0
        multiplier = 1
        while len(pq) > 0:
            _priority, value, pq = pq.pop()
            # use multiplier to ensure the correct order
            s += value * multiplier
            multiplier += 1
        pq.discard_empty()
        return s

    run_int_fn(
        main,
        # multiplier * value for ordered values in priority queue
        sum((m + 1) * v for m, v in enumerate(reversed(list(range(10))))),
    )


def test_priority_queue_iter(run_int_fn) -> None:
    @guppy
    def main() -> int:
        pq: PriorityQueue[int, 10] = empty_priority_queue()
        for i in range(10):
            # values are in order, priority is reversed
            pq = pq.push(i, 9 - i)
        s = 0
        multiplier = 1
        for priority, value in pq:
            # use multiplier to ensure the correct order
            s += value * multiplier
            multiplier += 1
        return s

    run_int_fn(
        main,
        # multiplier * value for ordered values in priority queue
        sum((m + 1) * v for m, v in enumerate(reversed(list(range(10))))),
    )


def test_queue(run_int_fn) -> None:
    @guppy
    def main() -> int:
        queue: Queue[int, 10] = empty_queue()
        for i in range(10):
            queue = queue.push(i)
        s = 0
        i = 1
        while len(queue) > 0:
            x, queue = queue.pop()
            s += x * i
            i += 1
        queue.discard_empty()
        return s

    run_int_fn(
        main,
        # multiplier * value for ordered values in the queue
        sum((i + 1) * x for i, x in enumerate(list(range(10)))),
    )


def test_queue_iter(run_int_fn) -> None:
    @guppy
    def main() -> int:
        queue: Queue[int, 10] = empty_queue()
        for i in range(10):
            queue = queue.push(i)
        s = 0
        i = 1
        for x in queue:
            s += x * i
            i += 1
        return s

    run_int_fn(
        main,
        # multiplier * value for ordered values in the queue
        sum((i + 1) * x for i, x in enumerate(list(range(10)))),
    )


def test_queue_full() -> None:
    @guppy
    def main() -> None:
        queue: Queue[int, 1] = empty_queue()
        for i in range(2):
            queue = queue.push(i)

        queue.discard_empty()

    with pytest.raises(
        EmulatorError, match=r"Panic \(#1001\): Queue.push: max size reached"
    ):
        main.emulator(n_qubits=0).stabilizer_sim().with_seed(42).run()


def test_queue_empty() -> None:
    @guppy
    def main() -> None:
        queue: Queue[int, 1] = empty_queue()
        for i in range(1):
            queue = queue.push(i)

        for _ in range(2):
            _, queue = queue.pop()

        queue.discard_empty()

    with pytest.raises(
        EmulatorError, match=r"Panic \(#1001\): Queue.pop: queue is empty"
    ):
        main.emulator(n_qubits=0).stabilizer_sim().with_seed(42).run()


def test_queue_circular(run_int_fn) -> None:
    @guppy
    def main() -> int:
        # Use a small MAX_SIZE to force wrap-around
        q: Queue[int, 5] = empty_queue()
        # Fill half, pop some, then push more to wrap
        for i in range(3):
            q = q.push(i)
        # Pop two elements
        for _ in range(2):
            _, q = q.pop()
        # Push again to cause wrap-around
        for i in range(3, 5):
            q = q.push(i)
        # Drain and sum to verify order
        total = 0
        multiplier = 1
        while len(q) > 0:
            x, q = q.pop()
            total += x * multiplier
            multiplier += 1
        return total

    # Expected order: remaining elements are [2,3,4]; sum with multipliers 1,2,3
    run_int_fn(main, 2 * 1 + 3 * 2 + 4 * 3)
