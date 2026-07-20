"""Statically analyze calculation entries used by executable archives."""

import ast
from dataclasses import dataclass
from pathlib import Path


_THUMBNAIL_CODE_LINE_LIMIT = 14


@dataclass(frozen=True)
class ArchiveEntryPreview:
    """Describe the static entry information shown in an archive thumbnail.

    Attributes:
        entry_name: Selected ``@uzon_calc`` function name.
        title: Statically resolved report title.
        source_excerpt: Leading source lines beginning at the decorator.
        description: Optional report description supplied by an archive owner.
    """

    entry_name: str
    title: str
    source_excerpt: str
    description: str | None = None


@dataclass(frozen=True)
class ArchiveScriptAnalysis:
    """Describe calculation entries and executable behavior in one script.

    Attributes:
        entry_names: Top-level ``@uzon_calc`` entry names in source order.
        has_main_guard: Whether the script contains a standard ``__main__`` guard.
        preview: Thumbnail metadata for the first entry, or ``None`` when absent.
    """

    entry_names: tuple[str, ...]
    has_main_guard: bool
    preview: ArchiveEntryPreview | None


class _EntryCallCollector(ast.NodeVisitor):
    """Collect calls from an entry body without descending into nested scopes."""

    def __init__(self) -> None:
        """Initialize an empty source-call collection.

        Args:
            None.

        Returns:
            None.

        Raises:
            None.
        """
        self.calls: list[ast.Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Record a call and continue through expressions in the same scope.

        Args:
            node: Call expression found in the selected entry body.

        Returns:
            None.

        Raises:
            None.
        """
        self.calls.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Skip calls owned by a nested synchronous function.

        Args:
            node: Nested function definition.

        Returns:
            None.

        Raises:
            None.
        """

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Skip calls owned by a nested asynchronous function.

        Args:
            node: Nested asynchronous function definition.

        Returns:
            None.

        Raises:
            None.
        """

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Skip calls owned by a nested class definition.

        Args:
            node: Nested class definition.

        Returns:
            None.

        Raises:
            None.
        """

    def visit_Lambda(self, node: ast.Lambda) -> None:
        """Skip calls owned by a nested lambda body.

        Args:
            node: Nested lambda expression.

        Returns:
            None.

        Raises:
            None.
        """


def _decorator_target_name(decorator: ast.expr) -> str | None:
    """Return the terminal name referenced by a decorator expression.

    Args:
        decorator: Decorator expression, optionally including a call.

    Returns:
        Terminal identifier for a name or attribute decorator, otherwise ``None``.

    Raises:
        None.
    """
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def _is_main_guard_node(node: ast.stmt) -> bool:
    """Return whether a statement is a standard ``__main__`` equality guard.

    Args:
        node: Top-level statement to inspect.

    Returns:
        ``True`` for either ordering of ``__name__ == "__main__"``.

    Raises:
        None.
    """
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    test = node.test
    if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    if len(test.comparators) != 1:
        return False

    left = test.left
    right = test.comparators[0]
    is_forward_guard = (
        isinstance(left, ast.Name)
        and left.id == "__name__"
        and isinstance(right, ast.Constant)
        and right.value == "__main__"
    )
    is_reverse_guard = (
        isinstance(left, ast.Constant)
        and left.value == "__main__"
        and isinstance(right, ast.Name)
        and right.id == "__name__"
    )
    return is_forward_guard or is_reverse_guard


def _call_target_name(call: ast.Call) -> str | None:
    """Return the terminal identifier invoked by a call expression.

    Args:
        call: Call expression to inspect.

    Returns:
        Function or attribute name, otherwise ``None``.

    Raises:
        None.
    """
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _literal_string_argument(call: ast.Call, keyword_name: str) -> str | None:
    """Read a literal string from the first argument or a named keyword.

    Args:
        call: Call expression containing the possible value.
        keyword_name: Canonical keyword used by the target API.

    Returns:
        Non-empty literal string when statically available, otherwise ``None``.

    Raises:
        None.
    """
    values: list[ast.expr] = []
    if call.args:
        values.append(call.args[0])
    values.extend(
        keyword.value for keyword in call.keywords if keyword.arg == keyword_name
    )
    for value in values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            title = value.value.strip()
            if title:
                return title
    return None


def _collect_entry_calls(
    entry_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[ast.Call]:
    """Collect same-scope entry calls in deterministic source order.

    Args:
        entry_node: Selected top-level calculation entry.

    Returns:
        Calls found in the entry body, excluding nested function and class scopes.

    Raises:
        None.
    """
    collector = _EntryCallCollector()
    for statement in entry_node.body:
        collector.visit(statement)
    return sorted(
        collector.calls,
        key=lambda call: (call.lineno, call.col_offset),
    )


def _extract_entry_title(
    entry_node: ast.FunctionDef | ast.AsyncFunctionDef,
    script_path: Path,
) -> str:
    """Resolve the preview title using the configured static fallback order.

    Args:
        entry_node: First top-level ``@uzon_calc`` entry.
        script_path: Source file used for the final filename fallback.

    Returns:
        First literal ``H1`` title, then ``doc_title``, decorator name, or stem.

    Raises:
        None.
    """
    calls = _collect_entry_calls(entry_node)
    for target_name, keyword_name in (("H1", "text"), ("doc_title", "title")):
        for call in calls:
            if _call_target_name(call) != target_name:
                continue
            title = _literal_string_argument(call, keyword_name)
            if title is not None:
                return title

    for decorator in entry_node.decorator_list:
        if _decorator_target_name(decorator) != "uzon_calc":
            continue
        if isinstance(decorator, ast.Call):
            title = _literal_string_argument(decorator, "name")
            if title is not None:
                return title
    return script_path.stem


def _extract_entry_source_excerpt(
    source_text: str,
    entry_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """Extract leading physical lines beginning at an entry decorator.

    Args:
        source_text: Complete UTF-8 script source.
        entry_node: First top-level calculation entry.

    Returns:
        At most fourteen expanded source lines, with truncation marked inline.

    Raises:
        None.
    """
    start_line = min(
        (decorator.lineno for decorator in entry_node.decorator_list),
        default=entry_node.lineno,
    )
    end_line = entry_node.end_lineno or entry_node.lineno
    source_lines = source_text.splitlines()
    excerpt_end = min(end_line, start_line + _THUMBNAIL_CODE_LINE_LIMIT - 1)
    excerpt_lines = [
        line.expandtabs(4).rstrip()
        for line in source_lines[start_line - 1 : excerpt_end]
    ]
    if excerpt_end < end_line and excerpt_lines:
        excerpt_lines[-1] = f"{excerpt_lines[-1]}  ..."
    return "\n".join(excerpt_lines)


def analyze_archive_script(script_path: Path) -> ArchiveScriptAnalysis:
    """Analyze executable entries and thumbnail metadata without running a script.

    Args:
        script_path: UTF-8 Python calculation script to analyze.

    Returns:
        Entry names, main-guard status, and first-entry preview metadata.

    Raises:
        OSError: When the script cannot be read.
        SyntaxError: When the script is not valid Python source.
    """
    source_text = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source_text, filename=str(script_path))
    entry_nodes = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(
            _decorator_target_name(decorator) == "uzon_calc"
            for decorator in node.decorator_list
        )
    ]
    preview = None
    if entry_nodes:
        first_entry = entry_nodes[0]
        preview = ArchiveEntryPreview(
            entry_name=first_entry.name,
            title=_extract_entry_title(first_entry, script_path),
            source_excerpt=_extract_entry_source_excerpt(source_text, first_entry),
        )
    return ArchiveScriptAnalysis(
        entry_names=tuple(node.name for node in entry_nodes),
        has_main_guard=any(_is_main_guard_node(node) for node in tree.body),
        preview=preview,
    )
