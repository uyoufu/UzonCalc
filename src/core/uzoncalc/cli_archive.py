"""UzonCalc CLI archive packaging helpers."""

import ast
import json
from pathlib import Path
import zipfile

_ARCHIVE_SUFFIX = ".uzc"
_ARCHIVE_BUNDLE_DIR = "__uzoncalc_bundle__"
_ARCHIVE_SOURCE_DIR = f"{_ARCHIVE_BUNDLE_DIR}/src"
_ARCHIVE_MANIFEST_PATH = f"{_ARCHIVE_BUNDLE_DIR}/manifest.json"
_MANIFEST_ENTRY_PATH = "entry_path"
_MANIFEST_AUTO_VIEW_ENTRY = "auto_view_entry"


def _is_uzon_calc_decorator(decorator: ast.expr) -> bool:
    """判断装饰器是否引用 uzon_calc。

    Args:
        decorator: AST 装饰器表达式。

    Returns:
        若装饰器形如 @uzon_calc、@uzon_calc(...)、@pkg.uzon_calc 或
        @pkg.uzon_calc(...)，则返回 True。

    Raises:
        None.
    """
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Name):
        return target.id == "uzon_calc"
    if isinstance(target, ast.Attribute):
        return target.attr == "uzon_calc"
    return False


def _is_main_name_node(node: ast.expr) -> bool:
    """判断表达式是否为 __name__。

    Args:
        node: 待检查的 AST 表达式。

    Returns:
        表达式为 __name__ 时返回 True，否则返回 False。

    Raises:
        None.
    """
    return isinstance(node, ast.Name) and node.id == "__name__"


def _is_main_string_node(node: ast.expr) -> bool:
    """判断表达式是否为字符串 "__main__"。

    Args:
        node: 待检查的 AST 表达式。

    Returns:
        表达式为 "__main__" 字符串常量时返回 True，否则返回 False。

    Raises:
        None.
    """
    return isinstance(node, ast.Constant) and node.value == "__main__"


def _is_main_guard_node(node: ast.stmt) -> bool:
    """判断语句是否为标准 __main__ 入口判断。

    Args:
        node: 待检查的 AST 语句。

    Returns:
        语句形如 if __name__ == "__main__" 或反向比较时返回 True。

    Raises:
        None.
    """
    if not isinstance(node, ast.If):
        return False
    test = node.test
    is_single_compare = (
        isinstance(test, ast.Compare)
        and len(test.ops) == 1
        and len(test.comparators) == 1
    )
    if not is_single_compare or not isinstance(test.ops[0], ast.Eq):
        return False
    left = test.left
    right = test.comparators[0]
    return (
        _is_main_name_node(left)
        and _is_main_string_node(right)
        or _is_main_string_node(left)
        and _is_main_name_node(right)
    )


def _analyze_archive_entry(script_path: Path) -> tuple[list[str], bool]:
    """分析待打包脚本的计算入口和 __main__ 入口。

    Args:
        script_path: 待打包的 Python 脚本路径。

    Returns:
        二元组：@uzon_calc 入口函数名列表、是否存在 __main__ 入口。

    Raises:
        SyntaxError: 当脚本不是合法 Python 源码时抛出。
        OSError: 当脚本无法读取时抛出。
    """
    tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
    entry_names = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(_is_uzon_calc_decorator(decorator) for decorator in node.decorator_list):
            entry_names.append(node.name)
    has_main_guard = any(_is_main_guard_node(node) for node in tree.body)
    return entry_names, has_main_guard


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
    for candidate_path in _module_file_candidates(source_root, module_parts):
        if candidate_path.is_file():
            return candidate_path.resolve()
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
            return []
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


def _collect_archive_source_files(source_root: Path, entry_script_path: Path) -> list[Path]:
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


def _build_archive_main_source(auto_view_entry: str | None) -> str:
    """生成 .uzc 归档的 __main__.py 源码。

    Args:
        auto_view_entry: 缺少源文件 __main__ 入口时需要自动 view() 的函数名。

    Returns:
        可写入归档根目录 __main__.py 的 Python 源码。

    Raises:
        None.
    """
    auto_entry_repr = repr(auto_view_entry)
    return f'''"""UzonCalc .uzc archive runner."""

import json
import runpy
import sys
import tempfile
import zipfile
from pathlib import Path


_ARCHIVE_SOURCE_DIR = "{_ARCHIVE_SOURCE_DIR}"
_ARCHIVE_MANIFEST_PATH = "{_ARCHIVE_MANIFEST_PATH}"
_MANIFEST_ENTRY_PATH = "{_MANIFEST_ENTRY_PATH}"
_AUTO_VIEW_ENTRY = {auto_entry_repr}


def _run_archive():
    """Extract and run the bundled UzonCalc report script."""
    archive_path = Path(sys.argv[0]).resolve()
    with tempfile.TemporaryDirectory(prefix="uzoncalc-uzc-") as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(temp_root)
        manifest_path = temp_root / _ARCHIVE_MANIFEST_PATH
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_root = temp_root / _ARCHIVE_SOURCE_DIR
        entry_path = source_root / manifest[_MANIFEST_ENTRY_PATH]

        sys.path.insert(0, str(source_root))
        sys.argv[0] = str(entry_path)
        if _AUTO_VIEW_ENTRY is None:
            runpy.run_path(str(entry_path), run_name="__main__")
            return

        module_globals = runpy.run_path(
            str(entry_path),
            run_name="_uzoncalc_bundled_script",
        )
        from uzoncalc import view

        view(module_globals[_AUTO_VIEW_ENTRY])


if __name__ == "__main__":
    _run_archive()
'''


def create_uzc_archive(
    script_path: Path,
    output_path: Path | None = None,
) -> Path:
    """创建可通过 python 运行的 .uzc 归档。

    Args:
        script_path: 待打包的 UzonCalc 计算书脚本。
        output_path: 可选的归档输出路径；为空时使用脚本同名 .uzc。

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

    entry_names, has_main_guard = _analyze_archive_entry(script_path)
    if not entry_names:
        raise RuntimeError("未找到 @uzon_calc 装饰的入口函数")
    if not has_main_guard and len(entry_names) > 1:
        raise RuntimeError(
            "存在多个 @uzon_calc 入口，请添加 if __name__ == \"__main__\" 显式入口"
        )

    archive_path = (
        output_path.resolve()
        if output_path
        else script_path.with_suffix(_ARCHIVE_SUFFIX)
    )
    if archive_path.suffix != _ARCHIVE_SUFFIX:
        archive_path = archive_path.with_suffix(_ARCHIVE_SUFFIX)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    source_root = script_path.parent.resolve()
    auto_view_entry = None if has_main_guard else entry_names[0]
    source_files = _collect_archive_source_files(source_root, script_path)
    manifest = {
        _MANIFEST_ENTRY_PATH: script_path.relative_to(source_root).as_posix(),
        _MANIFEST_AUTO_VIEW_ENTRY: auto_view_entry,
    }

    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr("__main__.py", _build_archive_main_source(auto_view_entry))
        archive.writestr(
            _ARCHIVE_MANIFEST_PATH,
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
        for source_file in source_files:
            relative_source_path = source_file.relative_to(source_root).as_posix()
            archive.write(source_file, f"{_ARCHIVE_SOURCE_DIR}/{relative_source_path}")

    return archive_path
