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


def test_priority_queue_repeated_push_pop(run_int_fn) -> None:
    @guppy
    def main() -> int:
        pq: PriorityQueue[int, 5] = empty_priority_queue()
        # Fill to capacity using priorities equal to values.
        for i in range(5):
            pq = pq.push(i, i)
        # Pop twice, then push a couple more values after freeing space.
        _, _, pq = pq.pop()
        _, _, pq = pq.pop()
        for i in range(5, 7):
            pq = pq.push(i, i)
        # Pop twice again and then push more values to exercise repeated cycles.
        _, _, pq = pq.pop()
        _, _, pq = pq.pop()
        for i in range(7, 9):
            pq = pq.push(i, i)
        # Drain remaining values in priority order and verify they are still ordered.
        total = 0
        multiplier = 1
        while len(pq) > 0:
            _, value, pq = pq.pop()
            total += value * multiplier
            multiplier += 1
        pq.discard_empty()
        return total

    run_int_fn(main, sum((m + 1) * v for m, v in enumerate(range(4, 9))))


def test_queue(run_int_fn) -> None:
    @guppy
    def main() -> int:
        queue: Queue[int, 10] = empty_queue()
        for i in range(9):
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
        sum((i + 1) * x for i, x in enumerate(list(range(9)))),
    )


def test_queue_iter(run_int_fn) -> None:
    @guppy
    def main() -> int:
        queue: Queue[int, 10] = empty_queue()
        for i in range(9):
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
        sum((i + 1) * x for i, x in enumerate(list(range(9)))),
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
        for i in range(0):
            queue = queue.push(i)

        for _ in range(2):
            _, queue = queue.pop()

        queue.discard_empty()

    with pytest.raises(
        EmulatorError, match=r"Panic \(#1001\): Queue.pop: queue is empty"
    ):
        main.emulator(n_qubits=0).stabilizer_sim().with_seed(42).run()


def test_queue_beyond_max_size(run_int_fn) -> None:
    @guppy
    def main() -> int:
        q: Queue[int, 5] = empty_queue()
        # Fill to the effective capacity of the queue.
        for i in range(4):
            q = q.push(i)
        # Pop twice to make room and advance the internal indices.
        for _ in range(2):
            _, q = q.pop()
        # Push more values after pops, which forces wrap-around inside the buffer.
        for i in range(4, 6):
            q = q.push(i)
        # Pop once and push again to force a second wrap-around cycle.
        _, q = q.pop()
        q = q.push(6)
        # Drain and verify FIFO order despite the internal wrap-around.
        total = 0
        multiplier = 1
        while len(q) > 0:
            x, q = q.pop()
            total += x * multiplier
            multiplier += 1
        return total

    # Expected values are [3, 4, 5, 6] in FIFO order.
    run_int_fn(main, 3 * 1 + 4 * 2 + 5 * 3 + 6 * 4)


def test_queue_wraparound_len(run_int_fn) -> None:
    @guppy
    def main() -> int:
        q: Queue[int, 5] = empty_queue()
        # Push three values so the internal head/tail indices move.
        for i in range(3):
            q = q.push(i)
        # Pop two values to advance the front pointer away from zero.
        for _ in range(2):
            _, q = q.pop()
        # Push two more values to wrap the end pointer around the circular buffer.
        for i in range(3, 5):
            q = q.push(i)
        # Length should still reflect the number of live elements.
        return len(q)

    run_int_fn(main, 3)


def test_queue_wraparound_iter(run_int_fn) -> None:
    @guppy
    def main() -> int:
        q: Queue[int, 5] = empty_queue()
        # Set up a wrapped queue by pushing, popping, then pushing again.
        for i in range(3):
            q = q.push(i)
        for _ in range(2):
            _, q = q.pop()
        for i in range(3, 5):
            q = q.push(i)
        # Iterate over the queue and verify FIFO order after wrap-around.
        total = 0
        multiplier = 1
        for x in q:
            total += x * multiplier
            multiplier += 1
        return total

    # Expected values are [2, 3, 4] in FIFO order.
    run_int_fn(main, 2 * 1 + 3 * 2 + 4 * 3)


def test_queue_wraparound_discard_empty(run_int_fn) -> None:
    @guppy
    def main() -> int:
        q: Queue[int, 5] = empty_queue()
        # Create a wrapped queue, then empty it by popping all remaining values.
        for i in range(3):
            q = q.push(i)
        for _ in range(2):
            _, q = q.pop()
        for i in range(3, 5):
            q = q.push(i)
        while len(q) > 0:
            _, q = q.pop()
        # Ensure discard_empty works even after the buffer head/tail have wrapped.
        q.discard_empty()
        return 0

    run_int_fn(main, 0)
