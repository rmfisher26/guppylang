from guppylang.decorator import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import qubit,discard_array

@guppy
def main() -> None:
  qs = array(qubit() for _ in range(10))
  q1 = qs[0]
  q2 = qs[0]
  discard_array(qs)

main.compile()