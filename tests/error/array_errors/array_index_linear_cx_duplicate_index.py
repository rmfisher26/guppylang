from guppylang.decorator import guppy
from guppylang.std.angles import angle
from guppylang.std.builtins import array
from guppylang.std.quantum import *
from guppylang.std.qsystem import *
from math import pi
import guppylang
from guppylang.std.builtins import array
guppylang.enable_experimental_features()

@guppy
def main() -> None:
    external_reg = array((qubit() for _ in range(2)))
    cx(external_reg[0], external_reg[0])
    measure_array(external_reg)

main.compile()