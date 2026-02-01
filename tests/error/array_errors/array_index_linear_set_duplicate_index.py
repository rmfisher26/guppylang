from guppylang.decorator import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import qubit,discard_array

@guppy
def main() -> None:
  qs = array(qubit() for _ in range(10))
  qs[0] = qubit()
  qs[1] = qubit()
  qs[2] = qubit()
  qs[0] = qubit()
  discard_array(qs)

main.compile()