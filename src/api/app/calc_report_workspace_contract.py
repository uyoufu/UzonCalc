"""Stable constants for the root-package calculation workspace contract."""

CALCBOOK_FORMAT_VERSION = 2
CALCBOOK_PATH = "calcbook.json"
ROOT_PACKAGE_PATH = "__init__.py"
DEFAULT_ENTRY_PATH = "main.py"
RESERVED_RUNTIME_ROOTS = frozenset({"manifest.json", "__uzon_deps__"})
