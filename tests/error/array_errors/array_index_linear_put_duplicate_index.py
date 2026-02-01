from guppylang.decorator import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import qubit,discard_array

@guppy
def main() -> None:
    qs = array(qubit() for _ in range(10))
    q1 = qubit()
    qs.put(q1, 0)
    q2 = qubit()
    qs.put(q2, 0)
    
    discard_array(qs)

main.compile()