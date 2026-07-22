"""Tests for standard package-relative imports in sandbox workspaces."""

import asyncio
from pathlib import Path
import sys
from types import ModuleType

from app.sandbox.core.dynamic_import import DynamicImportSession, clear_module_cache
from app.sandbox.core.runner import resolve_workspace_module_identity


def test_resolve_workspace_module_identity_uses_root_package_path(
    tmp_path: Path,
) -> None:
    """A root entry should receive an isolated workspace package identity."""
    entry = tmp_path / "main.py"
    entry.parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "__init__.py").write_text("", encoding="utf-8")
    entry.write_text("", encoding="utf-8")

    module_name, source_root = resolve_workspace_module_identity(
        str(entry), str(tmp_path), "execution-id"
    )

    assert module_name.startswith("__uzon_workspace_")
    assert module_name.endswith(".main")
    assert source_root == str(tmp_path.resolve())


def test_dynamic_import_session_supports_relative_imports(tmp_path: Path) -> None:
    """The loader should execute a package entry containing ``from .`` imports."""
    source_root = tmp_path
    (source_root / "__init__.py").write_text("", encoding="utf-8")
    (source_root / "values.py").write_text("VALUE = 42\n", encoding="utf-8")
    entry = source_root / "main.py"
    entry.write_text("from .values import VALUE\nRESULT = VALUE\n", encoding="utf-8")

    async def load_module() -> None:
        """Load the test entry through the production dynamic importer."""
        async with DynamicImportSession(
            module_name="__uzon_workspace_test.main",
            script_path=str(entry),
            package_root=str(tmp_path),
            source_root=str(source_root),
        ) as module:
            assert module.RESULT == 42

    try:
        asyncio.run(load_module())
    finally:
        clear_module_cache(str(entry))


def test_dynamic_import_session_keeps_host_modules_and_sys_path_unchanged(
    tmp_path: Path,
) -> None:
    """Relative workspace imports must not replace process-global host imports."""
    (tmp_path / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "values").mkdir()
    (tmp_path / "values" / "index.py").write_text(
        "VALUE = 42\n", encoding="utf-8"
    )
    entry = tmp_path / "main.py"
    entry.write_text(
        "from .values.index import VALUE\nRESULT = VALUE\n", encoding="utf-8"
    )
    host_values = ModuleType("values")
    host_values.VALUE = -1
    original_values = sys.modules.get("values")
    sys.modules["values"] = host_values
    original_sys_path = list(sys.path)

    async def load_module() -> None:
        """Load the entry while the colliding host module is installed."""
        async with DynamicImportSession(
            module_name="__uzon_workspace_collision.main",
            script_path=str(entry),
            package_root=str(tmp_path),
            source_root=str(tmp_path),
        ) as module:
            assert module.RESULT == 42
            assert sys.modules["values"] is host_values
            assert sys.path == original_sys_path

    try:
        asyncio.run(load_module())
        assert sys.modules["values"] is host_values
        assert sys.path == original_sys_path
    finally:
        clear_module_cache(str(entry))
        if original_values is None:
            sys.modules.pop("values", None)
        else:
            sys.modules["values"] = original_values
