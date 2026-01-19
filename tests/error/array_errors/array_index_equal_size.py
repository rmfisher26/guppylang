from guppylang.decorator import guppy
from guppylang.std.builtins import array

@guppy
def main() -> None:
   arr = array(i for i in range(5))
   return arr[5]

main.compile()