"""The string type."""

# mypy: disable-error-code="empty-body, misc, override, valid-type, no-untyped-def"

from __future__ import annotations

from typing import no_type_check

from guppylang_internals.decorator import custom_function, extend_type, hugr_op
from guppylang_internals.std._internal.checker import UnsupportedChecker
from guppylang_internals.std._internal.util import bool_logic_op
from guppylang_internals.tys.builtin import string_type_def

from guppylang import guppy


@extend_type(string_type_def)
class str:
    """A string, i.e. immutable sequences of Unicode code points."""

    @custom_function(checker=UnsupportedChecker(), higher_order_value=False)
    def __new__(x): ...

    # issue with bool_logic_op("eq")
    @hugr_op(bool_logic_op("eq"))
    # @hugr_op(string_logic_op("eq"))
    def __eq__(self: str, other: str) -> bool: ...

    @guppy
    @no_type_check
    def __ne__(self: str, other: str) -> bool:
        return not self == other


# add comparison operator to str definition
