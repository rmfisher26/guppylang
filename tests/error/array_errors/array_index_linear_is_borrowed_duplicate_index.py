from guppylang.decorator import guppy
from guppylang.std.builtins import array
from guppylang.std.quantum import qubit,discard_array

@guppy
def main() -> None:
  qs = array(qubit() for _ in range(10))
  qs.is_borrowed(0)
  qs.is_borrowed(0)
  discard_array(qs)

main.compile()