from guppylang.decorator import guppy
from guppylang.std.builtins import array, owned
from guppylang.std.quantum import qubit, h

import guppylang
guppylang.enable_experimental_features()


@guppy
def mixed_ownership(q1: qubit, q2: qubit @owned) -> tuple[qubit, qubit]:
    q1 = h(q1)
    return q1, q2


@guppy
def foo() -> None:
    qubits = array((qubit() for _ in range(3)))

    # ERROR: Cannot use qubits[0] twice with different ownership modes
    # - First argument borrows qubits[0] (will be returned)
    # - Second argument consumes qubits[0] (takes ownership)
    # This violates linearity: the same qubit cannot be both borrowed
    # and consumed simultaneously
    q1, q2 = mixed_ownership(qubits[0], qubits[0])


foo.compile()
