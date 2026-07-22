"""Normalize workspace-local imports for isolated package execution."""

from __future__ import annotations

import ast
from collections.abc import Iterable, Set
from pathlib import PurePosixPath


RESERVED_WORKSPACE_IMPORT_ROOTS = frozenset(
    {"uzoncalc", "calcdeps", "__uzon_deps__"}
)
_TEMPORARY_IMPORT_PREFIX = "__uzon_workspace_import_"


class DynamicWorkspaceImportError(ValueError):
    """Report a local dynamic import that cannot be package-scoped safely."""

    def __init__(self, source_path: str, module_name: str, line_number: int) -> None:
        """Initialize one source-located dynamic import error.

        Args:
            source_path: Workspace-relative Python source path.
            module_name: Absolute local module requested dynamically.
            line_number: One-based source line containing the call.

        Returns:
            None.

        Raises:
            None.
        """
        self.source_path = source_path
        self.module_name = module_name
        self.line_number = line_number
        super().__init__(source_path, module_name, line_number)

    def __str__(self) -> str:
        """Return an actionable source-located error message.

        Returns:
            Human-readable error text.

        Raises:
            None.
        """
        return (
            f"Dynamic workspace import must be package-relative: "
            f"{self.source_path}:{self.line_number}: {self.module_name}"
        )


def workspace_import_roots(paths: Iterable[str]) -> frozenset[str]:
    """Return top-level import names provided by workspace Python paths.

    Args:
        paths: Workspace-root-relative file paths.

    Returns:
        Valid non-reserved top-level Python import names.

    Raises:
        None.
    """
    roots: set[str] = set()
    for raw_path in paths:
        path = PurePosixPath(raw_path)
        if path.suffix != ".py" or not path.parts:
            continue
        module_parts = path.with_suffix("").parts
        if not all(part.isidentifier() for part in module_parts):
            continue
        root_name = module_parts[0]
        if root_name != "__init__":
            roots.add(root_name)
    roots.difference_update(RESERVED_WORKSPACE_IMPORT_ROOTS)
    return frozenset(roots)


def rewrite_workspace_imports_in_tree(
    tree: ast.Module,
    *,
    source_path: str,
    import_roots: Set[str],
) -> bool:
    """Rewrite static local absolute imports in an existing syntax tree.

    Args:
        tree: Parsed Python module to update in place.
        source_path: Workspace-relative path used to calculate package depth.
        import_roots: Top-level names owned by the workspace.

    Returns:
        Whether at least one import statement was rewritten.

    Raises:
        ValueError: If ``source_path`` is not an importable Python path.
        DynamicWorkspaceImportError: If a literal dynamic local import is absolute.
    """
    path = PurePosixPath(source_path)
    module_parts = path.with_suffix("").parts
    if path.suffix != ".py" or not module_parts or not all(
        part.isidentifier() for part in module_parts
    ):
        raise ValueError(f"Workspace source path is not importable: {source_path}")
    used_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    transformer = _WorkspaceImportRewriter(
        source_path=path.as_posix(),
        relative_level=len(path.parent.parts) + 1,
        import_roots=set(import_roots) - RESERVED_WORKSPACE_IMPORT_ROOTS,
        used_names=used_names,
    )
    transformer.visit(tree)
    return transformer.has_changes


def rewrite_workspace_source(
    source: str,
    *,
    source_path: str,
    import_roots: Set[str],
) -> str:
    """Return source with static local absolute imports made package-relative.

    Args:
        source: UTF-8 Python source text.
        source_path: Workspace-relative path used for diagnostics and package depth.
        import_roots: Top-level names owned by the workspace.

    Returns:
        Original source when unchanged, otherwise normalized generated source.

    Raises:
        SyntaxError: If ``source`` is invalid Python.
        ValueError: If ``source_path`` is not importable.
        DynamicWorkspaceImportError: If a literal dynamic local import is absolute.
    """
    tree = ast.parse(source, filename=source_path)
    if not rewrite_workspace_imports_in_tree(
        tree, source_path=source_path, import_roots=import_roots
    ):
        return source
    ast.fix_missing_locations(tree)
    generated = ast.unparse(tree) + "\n"
    compile(generated, source_path, "exec")
    return generated


class _WorkspaceImportRewriter(ast.NodeTransformer):
    """Rewrite imports owned by one root-package workspace."""

    def __init__(
        self,
        *,
        source_path: str,
        relative_level: int,
        import_roots: set[str],
        used_names: set[str],
    ) -> None:
        """Initialize the source-specific import transformer.

        Args:
            source_path: Workspace-relative source path.
            relative_level: Leading-dot count required to reach the workspace root.
            import_roots: Top-level names owned by the workspace.
            used_names: Names already present in the source module.

        Returns:
            None.

        Raises:
            None.
        """
        self.source_path = source_path
        self.relative_level = relative_level
        self.import_roots = import_roots
        self.used_names = used_names
        self.has_changes = False
        self._temporary_index = 0

    def visit_Import(self, node: ast.Import) -> ast.AST | list[ast.stmt]:
        """Rewrite local imports while preserving Python binding semantics.

        Args:
            node: Absolute import statement.

        Returns:
            Original node or replacement statements.

        Raises:
            None.
        """
        statements: list[ast.stmt] = []
        for imported in node.names:
            if not self._is_workspace_module(imported.name):
                statements.append(
                    ast.copy_location(ast.Import(names=[imported]), node)
                )
                continue
            self.has_changes = True
            statements.extend(self._relative_import_statements(imported, node))
        return statements[0] if len(statements) == 1 else statements

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        """Make one local ``from`` import relative to the workspace package.

        Args:
            node: From-import statement.

        Returns:
            Updated or original statement.

        Raises:
            None.
        """
        if node.level or not node.module or not self._is_workspace_module(node.module):
            return node
        self.has_changes = True
        node.level = self.relative_level
        return node

    def visit_Call(self, node: ast.Call) -> ast.AST:
        """Reject literal dynamic imports that target a local absolute name.

        Args:
            node: Function call expression.

        Returns:
            Visited call when it is not an unsafe workspace import.

        Raises:
            DynamicWorkspaceImportError: If the call names a local absolute module.
        """
        self.generic_visit(node)
        function_name = None
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        if function_name not in {"__import__", "import_module"} or not node.args:
            return node
        module_argument = node.args[0]
        if not isinstance(module_argument, ast.Constant) or not isinstance(
            module_argument.value, str
        ):
            return node
        module_name = module_argument.value
        if module_name.startswith(".") or not self._is_workspace_module(module_name):
            return node
        raise DynamicWorkspaceImportError(
            self.source_path, module_name, getattr(node, "lineno", 1)
        )

    def _relative_import_statements(
        self, imported: ast.alias, location: ast.Import
    ) -> list[ast.stmt]:
        """Build relative statements equivalent to one absolute import alias.

        Args:
            imported: Imported module and optional binding alias.
            location: Original node supplying source location metadata.

        Returns:
            Replacement import and cleanup statements.

        Raises:
            None.
        """
        parts = imported.name.split(".")
        if imported.asname or len(parts) == 1:
            module_name = ".".join(parts[:-1]) or None
            alias = ast.alias(name=parts[-1], asname=imported.asname)
            return [
                ast.copy_location(
                    ast.ImportFrom(
                        module=module_name,
                        names=[alias],
                        level=self.relative_level,
                    ),
                    location,
                )
            ]

        temporary_name = self._next_temporary_name()
        load_leaf = ast.copy_location(
            ast.ImportFrom(
                module=".".join(parts[:-1]),
                names=[ast.alias(name=parts[-1], asname=temporary_name)],
                level=self.relative_level,
            ),
            location,
        )
        bind_root = ast.copy_location(
            ast.ImportFrom(
                module=None,
                names=[ast.alias(name=parts[0])],
                level=self.relative_level,
            ),
            location,
        )
        cleanup = ast.copy_location(
            ast.Delete(targets=[ast.Name(id=temporary_name, ctx=ast.Del())]),
            location,
        )
        return [load_leaf, bind_root, cleanup]

    def _next_temporary_name(self) -> str:
        """Return a generated binding absent from the user module.

        Returns:
            Collision-free temporary import binding.

        Raises:
            None.
        """
        while True:
            name = f"{_TEMPORARY_IMPORT_PREFIX}{self._temporary_index}"
            self._temporary_index += 1
            if name not in self.used_names:
                self.used_names.add(name)
                return name

    def _is_workspace_module(self, module_name: str) -> bool:
        """Return whether an absolute module belongs to the workspace.

        Args:
            module_name: Dotted absolute module name.

        Returns:
            Whether its top-level name is workspace-owned.

        Raises:
            None.
        """
        return module_name.split(".", 1)[0] in self.import_roots
