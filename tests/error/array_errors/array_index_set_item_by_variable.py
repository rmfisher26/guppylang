from guppylang.decorator import guppy
from guppylang.std.builtins import array

@guppy
def main() -> None:
      arr = array(i for i in range(10))
      x = 50
      return arr[x] 

main.compile()