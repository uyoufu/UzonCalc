"""Validate that core tests use the installed package identity."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
import subprocess
import sys

import uzoncalc

EXPECTED_PUBLIC_API = frozenset(
    """
    AutoLabel Bold Br CalcContext Code Div DocumentExporter Field FieldType Figure
    Green H H1 H2 H3 H4 H5 H6 HtmlDocumentExporter HtmlFragment ISavefig Img Info
    Input Italic LaTex LabelKind Markdown P Plot Props Red Row Span Subtitle Table
    TableBodyRows TableCellValue TableHeaderRows Td Title TocPageNumberResolver Tr
    UI UIPayloads Window Yellow alias bold br code decimal disable_formula_expression
    disable_fstring_equation disable_substitution div doc_title
    enable_formula_expression enable_fstring_equation enable_substitution end_inline
    figure_prefix font_family get_current_instance green h h1 h2 h3 h4 h5 h6 head
    hide img info inline input italic laTex markdown p page_size plot props red row run
    run_sync show span style subtitle table table_prefix td th title toc tr unit
    uzon_calc uzon_calc_core uzon_calc_func view yellow
    """.split()
)


def test_core_tests_do_not_import_source_tree_package_name() -> None:
    """Reject imports that create a second ``core.uzoncalc`` module graph."""
    tests_dir = Path(__file__).parent
    offenders: list[str] = []
    for path in tests_dir.rglob("*.py"):
        tree = ast.parse(path.read_text("utf-8"), filename=str(path))
        imported_modules = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        imported_modules.extend(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        if any(name == "core.uzoncalc" or name.startswith("core.uzoncalc.") for name in imported_modules):
            offenders.append(path.name)

    assert offenders == []


def test_published_package_has_one_module_identity() -> None:
    """Ensure repeated imports resolve to the installed ``uzoncalc`` package."""
    assert importlib.import_module("uzoncalc") is uzoncalc
    assert "core.uzoncalc" not in sys.modules


def test_public_api_matches_curated_snapshot() -> None:
    """Keep additions and removals from the root API deliberate."""
    assert set(uzoncalc.__all__) == EXPECTED_PUBLIC_API


def test_base_import_does_not_load_optional_feature_modules() -> None:
    """Importing the root package should not load optional dependency stacks."""
    script = """
import sys
import uzoncalc
optional = {'fitz', 'matplotlib', 'openpyxl', 'playwright', 'svg', 'xlwings'}
loaded = sorted(optional.intersection(sys.modules))
raise SystemExit(f'optional modules loaded: {loaded}' if loaded else 0)
"""

    subprocess.run([sys.executable, "-c", script], check=True)
