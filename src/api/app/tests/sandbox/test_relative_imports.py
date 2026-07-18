"""Tests for standard package-relative imports in sandbox workspaces."""

import asyncio
from pathlib import Path

from app.sandbox.core.dynamic_import import DynamicImportSession, clear_module_cache
from app.sandbox.core.runner import resolve_workspace_module_identity


def test_resolve_workspace_module_identity_uses_src_package_path(
    tmp_path: Path,
) -> None:
    """A nested entry should retain its normal Python package identity."""
    entry = tmp_path / "src" / "engineering" / "main.py"
    entry.parent.mkdir(parents=True)
    entry.write_text("", encoding="utf-8")

    module_name, source_root = resolve_workspace_module_identity(
        str(entry), str(tmp_path), "execution-id"
    )

    assert module_name == "engineering.main"
    assert source_root == str((tmp_path / "src").resolve())


def test_dynamic_import_session_supports_relative_imports(tmp_path: Path) -> None:
    """The loader should execute a package entry containing ``from .`` imports."""
    source_root = tmp_path / "src"
    package = source_root / "engineering"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "values.py").write_text("VALUE = 42\n", encoding="utf-8")
    entry = package / "main.py"
    entry.write_text("from .values import VALUE\nRESULT = VALUE\n", encoding="utf-8")

    async def load_module() -> None:
        """Load the test entry through the production dynamic importer."""
        async with DynamicImportSession(
            module_name="engineering.main",
            script_path=str(entry),
            package_root=str(tmp_path),
            source_root=str(source_root),
        ) as module:
            assert module.RESULT == 42

    try:
        asyncio.run(load_module())
    finally:
        clear_module_cache(str(entry))
