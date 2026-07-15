"""Pure source-to-source pre-instrumentation for managed CalcReport files."""

from __future__ import annotations

import ast
import copy
import re
from dataclasses import dataclass
from typing import Callable

from .ast_validator import validate_ast
from .ast_visitor import AstNodeVisitor
from .field_names import FieldNames

INSTRUMENTATION_FORMAT_VERSION = 1
_RESERVED_PREFIX = "__uzon_"
_MARKER_NAME = "__uzon_mark_preinstrumented__"


@dataclass(frozen=True)
class PreinstrumentResult:
    """Return generated Python source and coarse generated/original line mappings."""

    source: str
    source_map: list[dict[str, int | str]]
    instrumented_functions: list[str]


def mark_preinstrumented(function: Callable) -> Callable:
    """Mark a generated function so runtime decorators skip AST rebuilding.

    Args:
        function: Function whose body was transformed by the managed builder.

    Returns:
        The same function with the internal instrumentation marker.
    """
    setattr(function, FieldNames.uzon_instrumented, True)
    return function


def preinstrument_source(
    source: str,
    *,
    filename: str,
    scope_key: str,
    dependency_defaults: dict[str, str],
) -> PreinstrumentResult:
    """Transform decorated functions and statically scope calcdeps imports.

    Args:
        source: Original UTF-8 Python source.
        filename: Stable workspace-relative filename used in diagnostics.
        scope_key: Valid Python identifier for this SOURCE artifact scope.
        dependency_defaults: Dependency alias to default selector mapping.

    Returns:
        Generated source, source-map entries, and transformed function names.

    Raises:
        SyntaxError: If original or generated source is invalid.
        ValueError: If reserved names, dynamic imports, or invalid dependencies occur.
        ValidationError: If existing instrumentation rejects the function AST.
    """
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", scope_key):
        raise ValueError("scope_key must be a valid Python identifier")
    tree = ast.parse(source, filename=filename)
    _reject_reserved_names(tree)
    decorator_names, module_aliases = _discover_uzoncalc_imports(tree)
    tree = _CalcdepsImportRewriter(scope_key, dependency_defaults).visit(tree)
    instrumented: list[tuple[str, int, int]] = []
    for index, node in enumerate(tree.body):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _has_calc_decorator(node, decorator_names, module_aliases):
            continue
        transformed = copy.deepcopy(node)
        transformed = AstNodeVisitor().visit(transformed)
        transformed.decorator_list.append(ast.Name(id=_MARKER_NAME, ctx=ast.Load()))
        ast.copy_location(transformed.decorator_list[-1], node)
        validate_ast(ast.Module(body=[copy.deepcopy(transformed)], type_ignores=[]))
        tree.body[index] = transformed
        instrumented.append(
            (node.name, node.lineno, getattr(node, "end_lineno", node.lineno))
        )
    if instrumented:
        _inject_runtime_imports(tree)
    ast.fix_missing_locations(tree)
    generated = ast.unparse(tree) + "\n"
    compile(generated, filename, "exec")
    source_map = _build_function_source_map(generated, instrumented)
    return PreinstrumentResult(
        source=generated,
        source_map=source_map,
        instrumented_functions=[name for name, _, _ in instrumented],
    )


def _reject_reserved_names(tree: ast.Module) -> None:
    """Reject user-owned names reserved for generated instrumentation runtime."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id.startswith(_RESERVED_PREFIX):
            raise ValueError(f"Reserved instrumentation name is not allowed: {node.id}")
        if isinstance(node, ast.alias):
            bound_name = node.asname or node.name.split(".")[0]
            if bound_name.startswith(_RESERVED_PREFIX):
                raise ValueError(
                    f"Reserved instrumentation name is not allowed: {bound_name}"
                )


def _discover_uzoncalc_imports(tree: ast.Module) -> tuple[set[str], set[str]]:
    """Discover aliases that can refer to public calculation decorators."""
    decorator_names = {"uzon_calc", "uzon_calc_func"}
    module_aliases = {"uzoncalc"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name.endswith("uzoncalc"):
                    module_aliases.add(imported.asname or imported.name.split(".")[0])
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.endswith("uzoncalc")
        ):
            for imported in node.names:
                if imported.name in {"uzon_calc", "uzon_calc_func"}:
                    decorator_names.add(imported.asname or imported.name)
    return decorator_names, module_aliases


def _has_calc_decorator(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    decorator_names: set[str],
    module_aliases: set[str],
) -> bool:
    """Return whether a function has a statically recognized calc decorator."""
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id in decorator_names:
            return True
        if (
            isinstance(target, ast.Attribute)
            and target.attr in {"uzon_calc", "uzon_calc_func"}
            and isinstance(target.value, ast.Name)
            and target.value.id in module_aliases
        ):
            return True
    return False


def _inject_runtime_imports(tree: ast.Module) -> None:
    """Inject reserved imports required by generated recorder calls and marker."""
    imports = ast.parse(
        "from uzoncalc.handcalc.preinstrument import "
        "mark_preinstrumented as __uzon_mark_preinstrumented__\n"
        "from uzoncalc.handcalc.recorder import record_step as __uzon_record_step__\n"
        "from uzoncalc.handcalc import ir as __uzon_ir__\n"
        "from uzoncalc.handcalc import steps as __uzon_steps__\n"
    ).body
    insert_at = 0
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        insert_at = 1
    while (
        insert_at < len(tree.body)
        and isinstance(tree.body[insert_at], ast.ImportFrom)
        and tree.body[insert_at].module == "__future__"
    ):
        insert_at += 1
    tree.body[insert_at:insert_at] = imports


def _build_function_source_map(
    generated: str, functions: list[tuple[str, int, int]]
) -> list[dict[str, int | str]]:
    """Build stable function-level generated-to-original source-map entries."""
    generated_lines = generated.splitlines()
    entries: list[dict[str, int | str]] = []
    for function_name, original_start, original_end in functions:
        pattern = re.compile(rf"^\s*(?:async\s+)?def\s+{re.escape(function_name)}\b")
        generated_start = next(
            (
                index
                for index, line in enumerate(generated_lines, start=1)
                if pattern.search(line)
            ),
            1,
        )
        entries.append(
            {
                "function": function_name,
                "originalStart": original_start,
                "originalEnd": original_end,
                "generatedStart": generated_start,
            }
        )
    return entries


class _CalcdepsImportRewriter(ast.NodeTransformer):
    """Rewrite public calcdeps imports into an artifact-local namespace."""

    def __init__(self, scope_key: str, dependency_defaults: dict[str, str]):
        """Initialize the static import rewriter."""
        self.scope_key = scope_key
        self.dependency_defaults = dependency_defaults

    def visit_Import(self, node: ast.Import) -> ast.AST:
        """Rewrite each absolute calcdeps import and preserve explicit aliases."""
        for imported in node.names:
            if imported.name == "calcdeps" or imported.name.startswith("calcdeps."):
                if imported.name == "calcdeps":
                    raise ValueError("Bare import calcdeps is not supported")
                imported.name = self._rewrite_module(imported.name)
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        """Rewrite a from-calcdeps module path."""
        if node.level:
            return node
        if node.module == "calcdeps" or (
            node.module and node.module.startswith("calcdeps.")
        ):
            if node.module == "calcdeps":
                raise ValueError("from calcdeps import ... is not supported")
            node.module = self._rewrite_module(node.module)
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Reject dynamic loading of the reserved dependency namespace."""
        self.generic_visit(node)
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name in {"__import__", "import_module"} and node.args:
            argument = node.args[0]
            if not isinstance(argument, ast.Constant) or (
                isinstance(argument.value, str)
                and argument.value.startswith("calcdeps")
            ):
                raise ValueError("Dynamic calcdeps import is not supported")
        return node

    def _rewrite_module(self, module_name: str) -> str:
        """Resolve alias/default selector and return the internal module path."""
        parts = module_name.split(".")
        if len(parts) < 3:
            raise ValueError("calcdeps import must include an alias and module")
        alias = parts[1]
        if alias not in self.dependency_defaults:
            raise ValueError(f"Undeclared calcdeps alias: {alias}")
        remaining = parts[2:]
        if remaining[0] == "latest" or remaining[0].startswith("v_"):
            selector = remaining.pop(0)
        else:
            selector = self.dependency_defaults[alias]
        if not remaining:
            raise ValueError("calcdeps import must include an exported module")
        return ".".join(["__uzon_deps__", self.scope_key, alias, selector, *remaining])
