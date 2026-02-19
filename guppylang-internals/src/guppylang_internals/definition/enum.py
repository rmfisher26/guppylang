"""Guppy enum (sum type) definitions.

Enums are user-defined tagged unions. Each variant can carry zero or more
typed fields. Example:

    T = guppy.type_var("T")

    @guppy.enum
    class Result(Generic[T]):
        Ok  = {"value": T}
        Err = {"code": int}
        Nil = {}

Variant constructors are then accessible as ``Result.Ok(x)``, etc.
"""

import ast
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ClassVar

from hugr import Wire, ops

from guppylang_internals.ast_util import AstNode
from guppylang_internals.checker.core import Globals
from guppylang_internals.checker.errors.generic import UnexpectedError, UnsupportedError
from guppylang_internals.compiler.core import GlobalConstId
from guppylang_internals.definition.common import (
    CheckableDef,
    CompiledDef,
    DefId,
    ParsableDef,
)
from guppylang_internals.definition.custom import (
    CustomCallCompiler,
    CustomFunctionDef,
    DefaultCallChecker,
)
from guppylang_internals.definition.struct import (
    StructField,
    params_from_ast,
    parse_py_class,
    try_parse_generic_base,
)
from guppylang_internals.definition.ty import TypeDef
from guppylang_internals.diagnostic import Error, Note
from guppylang_internals.engine import DEF_STORE
from guppylang_internals.error import GuppyError, InternalGuppyError
from guppylang_internals.span import SourceMap, Span, to_span
from guppylang_internals.tys.arg import Argument
from guppylang_internals.tys.param import Parameter, check_all_args
from guppylang_internals.tys.parsing import TypeParsingCtx, type_from_ast
from guppylang_internals.tys.ty import (
    FuncInput,
    FunctionType,
    InputFlags,
    Type,
)

if sys.version_info >= (3, 12):
    from guppylang_internals.tys.parsing import parse_parameter


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UncheckedEnumVariant:
    """A single variant of an enum whose field types have not been checked yet."""

    name: str
    fields: list[tuple[str, ast.expr]]  # (field_name, type_ast)
    defined_at: AstNode  # the Assign node for error reporting


@dataclass(frozen=True)
class EnumVariant:
    """A single variant of an enum with resolved field types."""

    name: str
    fields: list[StructField]


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InvalidVariantDefinitionError(Error):
    title: ClassVar[str] = "Invalid enum variant"
    span_label: ClassVar[str] = (
        "Expected a variant definition like `VariantName = {{'field': type, ...}}`"
    )


@dataclass(frozen=True)
class DuplicateVariantError(Error):
    title: ClassVar[str] = "Duplicate variant"
    span_label: ClassVar[str] = (
        "Enum `{enum_name}` already contains a variant named `{variant_name}`"
    )
    enum_name: str
    variant_name: str

    @dataclass(frozen=True)
    class PrevDef(Note):
        span_label: ClassVar[str] = "Variant `{variant_name}` first defined here"
        variant_name: str


@dataclass(frozen=True)
class InvalidVariantFieldKeyError(Error):
    title: ClassVar[str] = "Invalid field name"
    span_label: ClassVar[str] = "Field keys must be string literals"


@dataclass(frozen=True)
class DuplicateVariantFieldError(Error):
    title: ClassVar[str] = "Duplicate field"
    span_label: ClassVar[str] = (
        "Variant `{variant_name}` already has a field named `{field_name}`"
    )
    variant_name: str
    field_name: str


@dataclass(frozen=True)
class RedundantEnumParamsError(Error):
    title: ClassVar[str] = "Generic parameters already specified"
    span_label: ClassVar[str] = "Duplicate specification of generic parameters"
    enum_name: str

    @dataclass(frozen=True)
    class PrevSpec(Note):
        span_label: ClassVar[str] = (
            "Parameters of `{enum_name}` are already specified here"
        )
        enum_name: str


# ---------------------------------------------------------------------------
# Raw enum definition (before parsing)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawEnumDef(TypeDef, ParsableDef):
    """A raw enum type definition that has not been parsed yet."""

    python_class: type
    params: None = field(default=None, init=False)

    def parse(self, globals: Globals, sources: SourceMap) -> "ParsedEnumDef":
        """Parses the raw class object into an AST and validates it."""
        frame = DEF_STORE.frames[self.id]
        cls_def = parse_py_class(self.python_class, frame, sources)
        if cls_def.keywords:
            raise GuppyError(UnexpectedError(cls_def.keywords[0], "keyword"))

        # Extract generic parameters (Python 3.12 style)
        params: list[Parameter] = []
        params_span: Span | None = None
        if sys.version_info >= (3, 12):
            if cls_def.type_params:
                first, last = cls_def.type_params[0], cls_def.type_params[-1]
                params_span = Span(to_span(first).start, to_span(last).end)
                param_vars_mapping: dict[str, Parameter] = {}
                for idx, param_node in enumerate(cls_def.type_params):
                    param = parse_parameter(
                        param_node, idx, globals, param_vars_mapping
                    )
                    param_vars_mapping[param.name] = param
                    params.append(param)

        # Handle Generic[...] base class (legacy style)
        match cls_def.bases:
            case []:
                pass
            case [base] if elems := try_parse_generic_base(base):
                if params_span is not None:
                    err: Error = RedundantEnumParamsError(base, self.name)
                    err.add_sub_diagnostic(
                        RedundantEnumParamsError.PrevSpec(params_span, self.name)
                    )
                    raise GuppyError(err)
                params = params_from_ast(elems, globals)
            case bases:
                err = UnsupportedError(bases[0], "Enum inheritance", singular=True)
                raise GuppyError(err)

        # Walk the class body to collect variant definitions
        variants: list[UncheckedEnumVariant] = []
        seen_variant_names: dict[str, AstNode] = {}

        for i, node in enumerate(cls_def.body):
            match i, node:
                case _, ast.Pass():
                    pass
                case 0, ast.Expr(value=ast.Constant(value=v)) if isinstance(v, str):
                    # Allow docstring at the start
                    pass
                case _, ast.Assign(
                    targets=[ast.Name(id=variant_name)], value=variant_value
                ):
                    # Variant definition: VariantName = {...}
                    if variant_name in seen_variant_names:
                        err = DuplicateVariantError(node, self.name, variant_name)
                        err.add_sub_diagnostic(
                            DuplicateVariantError.PrevDef(
                                seen_variant_names[variant_name], variant_name
                            )
                        )
                        raise GuppyError(err)

                    fields = _parse_variant_fields(variant_value, variant_name)
                    variants.append(UncheckedEnumVariant(variant_name, fields, node))
                    seen_variant_names[variant_name] = node
                case _, node:
                    raise GuppyError(InvalidVariantDefinitionError(node))

        return ParsedEnumDef(self.id, self.name, cls_def, params, variants)

    def check_instantiate(
        self, args: Sequence[Argument], loc: AstNode | None = None
    ) -> Type:
        raise InternalGuppyError("Tried to instantiate raw enum definition")


def _parse_variant_fields(
    node: ast.expr, variant_name: str
) -> list[tuple[str, ast.expr]]:
    """Parse the dict literal defining variant fields.

    Returns a list of (field_name, type_ast) pairs.
    Raises a GuppyError if the node is not a valid field dict.
    """
    if not isinstance(node, ast.Dict):
        raise GuppyError(InvalidVariantDefinitionError(node))

    fields: list[tuple[str, ast.expr]] = []
    seen_field_names: set[str] = set()

    for key_node, val_node in zip(node.keys, node.values, strict=True):
        # Keys must be string literals
        if not isinstance(key_node, ast.Constant) or not isinstance(
            key_node.value, str
        ):
            raise GuppyError(InvalidVariantFieldKeyError(key_node or node))

        field_name = key_node.value
        if field_name in seen_field_names:
            raise GuppyError(
                DuplicateVariantFieldError(key_node, variant_name, field_name)
            )
        seen_field_names.add(field_name)
        fields.append((field_name, val_node))

    return fields


# ---------------------------------------------------------------------------
# Parsed enum definition (fields collected, types not yet resolved)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedEnumDef(TypeDef, CheckableDef):
    """An enum definition whose variant field types have not been checked yet."""

    defined_at: ast.ClassDef
    params: Sequence[Parameter]
    variants: Sequence[UncheckedEnumVariant]

    def check(self, globals: Globals) -> "CheckedEnumDef":
        """Type-checks all variant field types."""
        param_var_mapping = {p.name: p for p in self.params}
        ctx = TypeParsingCtx(globals, param_var_mapping)

        checked_variants: list[EnumVariant] = []
        for variant in self.variants:
            checked_fields = [
                StructField(field_name, type_from_ast(field_type_ast, ctx))
                for field_name, field_type_ast in variant.fields
            ]
            checked_variants.append(EnumVariant(variant.name, checked_fields))

        return CheckedEnumDef(
            self.id, self.name, self.defined_at, self.params, checked_variants
        )

    def check_instantiate(
        self, args: Sequence[Argument], loc: AstNode | None = None
    ) -> Type:
        """Checks if the enum can be instantiated with the given arguments."""
        check_all_args(self.params, args, self.name, loc)
        globals = Globals(DEF_STORE.frames[self.id])
        checked_def = self.check(globals)
        from guppylang_internals.tys.ty import EnumType

        return EnumType(args, checked_def)


# ---------------------------------------------------------------------------
# Checked enum definition (fully resolved, generates constructors)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckedEnumDef(TypeDef, CompiledDef):
    """A fully checked enum definition."""

    defined_at: ast.ClassDef
    params: Sequence[Parameter]
    variants: Sequence[EnumVariant]

    def check_instantiate(
        self, args: Sequence[Argument], loc: AstNode | None = None
    ) -> Type:
        """Checks if the enum can be instantiated with the given arguments."""
        check_all_args(self.params, args, self.name, loc)
        from guppylang_internals.tys.ty import EnumType

        return EnumType(args, self)

    def generated_methods(self) -> list[CustomFunctionDef]:
        """Auto-generated variant constructor functions."""
        from guppylang_internals.tys.ty import EnumType

        constructors: list[CustomFunctionDef] = []
        for tag, variant in enumerate(self.variants):

            class _VariantCompiler(CustomCallCompiler):
                """Compiler for a single enum variant constructor."""

                _tag: int
                _enum_defn: "CheckedEnumDef"

                def compile(self, args: list[Wire]) -> list[Wire]:
                    enum_type = EnumType(list(self.type_args), self._enum_defn)
                    hugr_sum = enum_type.to_hugr(self.ctx)
                    return [self.builder.add_op(ops.Tag(self._tag, hugr_sum), *args)]

            # Capture tag and defn in the closure via class attributes
            compiler_cls = type(
                f"_{variant.name}Compiler",
                (_VariantCompiler,),
                {"_tag": tag, "_enum_defn": self},
            )

            constructor_sig = FunctionType(
                inputs=[
                    FuncInput(
                        f.ty,
                        InputFlags.Owned if f.ty.linear else InputFlags.NoFlags,
                        f.name,
                    )
                    for f in variant.fields
                ],
                output=EnumType(
                    defn=self,
                    args=[p.to_bound(i) for i, p in enumerate(self.params)],
                ),
                params=self.params,
            )

            constructor_def = CustomFunctionDef(
                id=DefId.fresh(),
                name=variant.name,
                defined_at=self.defined_at,
                ty=constructor_sig,
                call_checker=DefaultCallChecker(),
                call_compiler=compiler_cls(),
                higher_order_value=True,
                higher_order_func_id=GlobalConstId.fresh(f"{self.name}.{variant.name}"),
                has_signature=True,
            )
            constructors.append(constructor_def)

        return constructors
