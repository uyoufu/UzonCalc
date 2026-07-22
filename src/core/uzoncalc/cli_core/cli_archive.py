"""UzonCalc CLI archive packaging helpers."""

import ast
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from .cli_archive_analysis import analyze_archive_script
from .cli_thumbnail import (
    THUMBNAIL_HEIGHT,
    THUMBNAIL_WIDTH,
    render_archive_thumbnail,
)
from .cli_workspace_archive import write_workspace_archive
from ..workspace_imports import rewrite_workspace_source, workspace_import_roots
from .workspace_contract import (
    CALCBOOK_FORMAT_VERSION,
    CALCBOOK_PATH,
    RESERVED_IMPORT_ROOTS,
    RESERVED_RUNTIME_ROOTS,
    ROOT_PACKAGE_PATH,
)

_ARCHIVE_SUFFIX = ".uzc"
_REPORT_ARCHIVE_KIND = "uzoncalc.report-closure"
_SCRIPT_FILES_PREFIX = "reports/root/"


def _module_file_candidates(source_root: Path, module_parts: list[str]) -> list[Path]:
    """根据模块名生成可能的本地 Python 文件路径。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        module_parts: 模块名按点号拆分后的片段。

    Returns:
        可能存在的模块文件路径列表，按普通模块、包模块顺序排列。

    Raises:
        None.
    """
    if not module_parts:
        return []
    module_path = source_root.joinpath(*module_parts)
    return [module_path.with_suffix(".py"), module_path / "__init__.py"]


def _package_init_paths(source_root: Path, module_path: Path) -> list[Path]:
    """收集模块路径上需要随包打包的 __init__.py 文件。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        module_path: 已解析出的本地模块文件路径。

    Returns:
        从上层包到下层包的 __init__.py 文件列表，仅包含实际存在的文件。

    Raises:
        ValueError: 当 module_path 不在 source_root 下时抛出。
    """
    relative_path = module_path.relative_to(source_root)
    package_parts = list(relative_path.parent.parts)
    if module_path.name == "__init__.py" and package_parts:
        package_parts = package_parts[:-1]

    init_paths = []
    for index in range(1, len(package_parts) + 1):
        init_path = source_root.joinpath(*package_parts[:index], "__init__.py")
        if init_path.is_file():
            init_paths.append(init_path)
    return init_paths


def _resolve_local_module(source_root: Path, module_parts: list[str]) -> Path | None:
    """解析模块名对应的本地 Python 文件。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        module_parts: 模块名按点号拆分后的片段。

    Returns:
        若模块位于 source_root 下则返回对应文件路径，否则返回 None。

    Raises:
        None.
    """
    if module_parts and module_parts[0] in RESERVED_IMPORT_ROOTS:
        return None
    candidates = (
        [source_root / ROOT_PACKAGE_PATH]
        if not module_parts
        else _module_file_candidates(source_root, module_parts)
    )
    for candidate_path in candidates:
        if candidate_path.is_file():
            resolved_path = candidate_path.resolve()
            try:
                resolved_path.relative_to(source_root)
            except ValueError as error:
                raise ValueError("本地导入不能指向工作区外部") from error
            if _contains_symbolic_link(source_root, candidate_path):
                raise ValueError("本地导入不能使用符号链接")
            return resolved_path
    return None


def _current_package_parts(source_root: Path, source_path: Path) -> list[str]:
    """计算当前文件所在包路径。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        source_path: 当前正在分析的 Python 文件。

    Returns:
        当前文件所在包名片段；入口目录下的普通脚本返回空列表。

    Raises:
        ValueError: 当 source_path 不在 source_root 下时抛出。
    """
    relative_path = source_path.relative_to(source_root)
    return list(relative_path.parent.parts)


def _resolve_import_from_modules(
    source_root: Path,
    source_path: Path,
    import_node: ast.ImportFrom,
) -> list[Path]:
    """解析 from import 语句引用的本地模块文件。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        source_path: 当前正在分析的 Python 文件。
        import_node: from import 语句 AST 节点。

    Returns:
        解析出的本地模块文件列表。

    Raises:
        ValueError: 当 source_path 不在 source_root 下时抛出。
    """
    module_parts = import_node.module.split(".") if import_node.module else []
    if import_node.level:
        package_parts = _current_package_parts(source_root, source_path)
        keep_count = len(package_parts) - import_node.level + 1
        if keep_count < 0:
            raise ValueError("相对导入不能越过工作区根目录")
        module_parts = package_parts[:keep_count] + module_parts

    resolved_paths = []
    base_module_path = _resolve_local_module(source_root, module_parts)
    if base_module_path is not None:
        resolved_paths.append(base_module_path)

    for alias in import_node.names:
        if alias.name == "*":
            continue
        child_module_path = _resolve_local_module(
            source_root,
            module_parts + alias.name.split("."),
        )
        if child_module_path is not None:
            resolved_paths.append(child_module_path)
    return resolved_paths


def _iter_imported_local_modules(source_root: Path, source_path: Path) -> list[Path]:
    """遍历当前文件静态导入的本地 Python 模块。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        source_path: 当前正在分析的 Python 文件。

    Returns:
        当前文件通过 import/from import 静态引用到的本地模块路径列表。

    Raises:
        SyntaxError: 当 source_path 不是合法 Python 源码时抛出。
        OSError: 当 source_path 无法读取时抛出。
    """
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    imported_paths = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_path = _resolve_local_module(
                    source_root,
                    alias.name.split("."),
                )
                if module_path is not None:
                    imported_paths.append(module_path)
        elif isinstance(node, ast.ImportFrom):
            imported_paths.extend(
                _resolve_import_from_modules(source_root, source_path, node)
            )
    return imported_paths


def _collect_archive_source_files(
    source_root: Path, entry_script_path: Path
) -> list[Path]:
    """收集打包所需的入口脚本和静态本地依赖。

    Args:
        source_root: 入口脚本所在的本地模块根目录。
        entry_script_path: 待打包的入口脚本路径。

    Returns:
        需要写入归档的 Python 文件绝对路径列表。

    Raises:
        SyntaxError: 当任一源码文件不是合法 Python 源码时抛出。
        OSError: 当任一源码文件无法读取时抛出。
    """
    pending_paths = [entry_script_path.resolve()]
    collected_paths: set[Path] = set()
    while pending_paths:
        current_path = pending_paths.pop()
        if current_path in collected_paths:
            continue
        collected_paths.add(current_path)

        for init_path in _package_init_paths(source_root, current_path):
            collected_paths.add(init_path.resolve())

        for imported_path in _iter_imported_local_modules(source_root, current_path):
            if imported_path not in collected_paths:
                pending_paths.append(imported_path)

    return sorted(
        collected_paths,
        key=lambda path: path.relative_to(source_root).as_posix(),
    )


def _resolve_archive_source_root(script_path: Path) -> Path:
    """Resolve the entry directory as the root-package workspace.

    Args:
        script_path: Absolute calculation entry path.

    Returns:
        Directory to expose on ``sys.path`` when the archive runs.

    Raises:
        None.
    """
    return script_path.parent.resolve()


def _contains_symbolic_link(workspace_root: Path, candidate: Path) -> bool:
    """Return whether a workspace path traverses a symbolic link.

    Args:
        workspace_root: Absolute workspace root.
        candidate: Lexical path located below the workspace root.

    Returns:
        Whether the candidate or one of its descendants from the root is a symlink.

    Raises:
        ValueError: If the lexical candidate is outside the workspace root.
    """
    relative = Path(os.path.abspath(candidate)).relative_to(workspace_root)
    current = workspace_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _collect_explicit_resource_files(
    workspace_root: Path,
    resource_paths: Iterable[Path],
    output_path: Path,
) -> list[Path]:
    """Resolve explicit resource files while preserving the workspace boundary.

    Args:
        workspace_root: Entry-script directory used as the archive root.
        resource_paths: Repeatable file or recursive directory selections.
        output_path: Archive output excluded from recursive selections.

    Returns:
        Deterministically sorted absolute regular-file paths.

    Raises:
        FileNotFoundError: If a selected resource does not exist.
        ValueError: If a resource escapes the root, uses symlinks, or is reserved.
    """
    collected: set[Path] = set()
    for resource_path in resource_paths:
        lexical_path = (
            resource_path
            if resource_path.is_absolute()
            else workspace_root / resource_path
        )
        if not lexical_path.exists():
            raise FileNotFoundError(f"资源路径不存在: {resource_path}")
        lexical_absolute = Path(os.path.abspath(lexical_path))
        try:
            lexical_absolute.relative_to(workspace_root)
        except ValueError as error:
            raise ValueError(f"资源路径必须位于工作区内: {resource_path}") from error
        if _contains_symbolic_link(workspace_root, lexical_absolute):
            raise ValueError(f"资源路径不能使用符号链接: {resource_path}")
        candidates = [lexical_absolute] if lexical_absolute.is_file() else lexical_absolute.rglob("*")
        for candidate in candidates:
            if candidate.is_symlink():
                raise ValueError(f"资源目录不能包含符号链接: {candidate}")
            if not candidate.is_file():
                continue
            resolved = candidate.resolve()
            try:
                relative = resolved.relative_to(workspace_root)
            except ValueError as error:
                raise ValueError(f"资源文件必须位于工作区内: {candidate}") from error
            if resolved == output_path:
                continue
            if relative.parts[0] in RESERVED_RUNTIME_ROOTS or relative.as_posix() == CALCBOOK_PATH:
                raise ValueError(f"资源路径由归档运行时保留: {relative.as_posix()}")
            collected.add(resolved)
    return sorted(collected, key=lambda path: path.relative_to(workspace_root).as_posix())


def create_uzc_archive(
    script_path: Path,
    output_path: Path | None = None,
    resource_paths: Iterable[Path] = (),
) -> Path:
    """创建带 PNG 缩略图且可通过 python 运行的 .uzc 归档。

    Args:
        script_path: 待打包的 UzonCalc 计算书脚本。
        output_path: 可选的归档输出路径；为空时使用脚本同名 .uzc。
        resource_paths: 可重复指定的工作区内资源文件或递归目录。

    Returns:
        已创建的 .uzc 归档路径。

    Raises:
        FileNotFoundError: 当 script_path 不存在时抛出。
        RuntimeError: 当脚本缺少 @uzon_calc 或无法自动生成入口时抛出。
        SyntaxError: 当脚本或本地依赖不是合法 Python 源码时抛出。
        OSError: 当文件读写失败时抛出。
    """
    script_path = script_path.resolve()
    if not script_path.is_file():
        raise FileNotFoundError(f"脚本文件不存在: {script_path}")

    analysis = analyze_archive_script(script_path)
    first_entry_name = next(iter(analysis.entry_names), None)
    if first_entry_name is None or analysis.preview is None:
        raise RuntimeError("未找到 @uzon_calc 装饰的入口函数")
    if not analysis.has_main_guard and len(analysis.entry_names) > 1:
        raise RuntimeError(
            '存在多个 @uzon_calc 入口，请添加 if __name__ == "__main__" 显式入口'
        )

    archive_path = (
        output_path.resolve()
        if output_path
        else script_path.with_suffix(_ARCHIVE_SUFFIX)
    )
    if archive_path.suffix.lower() not in {_ARCHIVE_SUFFIX, ".png"}:
        archive_path = archive_path.with_suffix(_ARCHIVE_SUFFIX)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    source_root = _resolve_archive_source_root(script_path)
    auto_view_entry = None if analysis.has_main_guard else first_entry_name
    source_files = _collect_archive_source_files(source_root, script_path)
    thumbnail_png = render_archive_thumbnail(analysis.preview)
    entry_relative_path = script_path.relative_to(source_root).as_posix()
    calcbook = {
        "formatVersion": CALCBOOK_FORMAT_VERSION,
        "entryPath": entry_relative_path,
    }
    source_contents = {
        source_file.relative_to(source_root).as_posix(): source_file.read_bytes()
        for source_file in source_files
    }
    source_contents.setdefault(
        ROOT_PACKAGE_PATH,
        (source_root / ROOT_PACKAGE_PATH).read_bytes()
        if (source_root / ROOT_PACKAGE_PATH).is_file()
        else b"",
    )
    import_roots = workspace_import_roots(source_contents)
    source_contents = {
        path: (
            rewrite_workspace_source(
                content.decode("utf-8"),
                source_path=path,
                import_roots=import_roots,
            ).encode("utf-8")
            if path.endswith(".py")
            else content
        )
        for path, content in source_contents.items()
    }
    for resource_file in _collect_explicit_resource_files(
        source_root, resource_paths, archive_path
    ):
        source_contents[resource_file.relative_to(source_root).as_posix()] = (
            resource_file.read_bytes()
        )
    source_contents[CALCBOOK_PATH] = (
        json.dumps(calcbook, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    artifact_hash = hashlib.sha256(
        b"".join(
            path.encode("utf-8") + b"\0" + content
            for path, content in sorted(source_contents.items())
        )
    ).hexdigest()
    report_key = artifact_hash[:24]
    manifest = {
        "kind": _REPORT_ARCHIVE_KIND,
        "rootNodeKey": "root",
        "permissions": {"canEdit": True, "canShare": True},
        "executable": {
            "filesPrefix": _SCRIPT_FILES_PREFIX,
            "entryPath": entry_relative_path,
            "autoViewEntry": auto_view_entry,
        },
        "reports": [
            {
                "nodeKey": "root",
                "reportKey": report_key,
                "name": script_path.stem,
                "description": None,
                "cover": None,
                "versionName": "1.0.0",
                "versionDescription": None,
                "isRoot": True,
                "isLatest": True,
                "filesPrefix": _SCRIPT_FILES_PREFIX,
                "calcbook": calcbook,
                "dependencies": [],
                "artifactHash": artifact_hash,
            }
        ],
        "thumbnail": {
            "entry_name": analysis.preview.entry_name,
            "title": analysis.preview.title,
            "width": THUMBNAIL_WIDTH,
            "height": THUMBNAIL_HEIGHT,
        },
    }
    files = {
        f"{_SCRIPT_FILES_PREFIX}{path}": content
        for path, content in source_contents.items()
    }
    write_workspace_archive(archive_path, thumbnail_png, manifest, files)

    return archive_path
