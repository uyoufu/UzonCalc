from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path

from rich.console import Console


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
PUBLISH_SCRIPT = SCRIPTS_DIR / "publish_examples.py"

sys.path.insert(0, str(SCRIPTS_DIR))


def load_publish_examples_module():
    """按脚本文件路径导入发布模块，避免要求 scripts 是 Python 包。"""
    spec = importlib.util.spec_from_file_location("publish_examples", PUBLISH_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_example(path: Path, source: str) -> Path:
    """写入用于 AST 检测的示例脚本。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_ast_detection_only_matches_real_uzon_calc_decorators(tmp_path):
    """示例发现只应匹配真实函数装饰器，不匹配字符串里的示例代码。"""
    module = load_publish_examples_module()
    examples_dir = tmp_path / "examples"

    decorated = write_example(
        examples_dir / "nested" / "decorated.py",
        "from uzoncalc import uzon_calc\n\n@uzon_calc\n"
        "def calc():\n    return None\n",
    )
    decorated_call = write_example(
        examples_dir / "decorated_call.py",
        "from uzoncalc import uzon_calc\n\n@uzon_calc(title='demo')\n"
        "async def calc():\n    return None\n",
    )
    write_example(
        examples_dir / "string_only.py",
        '"""Example:\n@uzon_calc\ndef fake():\n    pass\n"""\n',
    )
    write_example(
        examples_dir / "__init__.py",
        "from uzoncalc import uzon_calc\n\n@uzon_calc\n"
        "def ignored():\n    return None\n",
    )

    assert module.has_uzon_calc_decorator(decorated)
    assert [path.relative_to(examples_dir) for path in module.find_example_files(examples_dir)] == [
        decorated_call.relative_to(examples_dir),
        decorated.relative_to(examples_dir),
    ]


def test_output_path_preserves_nested_relative_structure(tmp_path):
    """嵌套示例应渲染为对应的临时 HTML 相对路径。"""
    module = load_publish_examples_module()
    examples_dir = tmp_path / "examples"
    output_dir = tmp_path / "html"
    example_path = examples_dir / "zh" / "units" / "beam.py"

    output_path = module.build_html_output_path(example_path, examples_dir, output_dir)

    assert output_path == output_dir / "zh" / "units" / "beam.html"


def test_archive_preserves_html_paths_without_temp_prefix(tmp_path):
    """打包时 zip 内路径应以 HTML 输出目录为根。"""
    module = load_publish_examples_module()
    output_dir = tmp_path / "html"
    (output_dir / "zh" / "units").mkdir(parents=True)
    (output_dir / "zh" / "units" / "beam.html").write_text("<html></html>", encoding="utf-8")
    archive_path = tmp_path / "examples-output.zip"

    html_files = module.create_examples_archive(output_dir, archive_path)

    assert html_files == [output_dir / "zh" / "units" / "beam.html"]
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == ["zh/units/beam.html"]


def test_entrypoint_uses_shared_keyboard_interrupt_helper(monkeypatch):
    """入口应复用共享 CLI 中断处理，将 Ctrl+C 转为退出码 130。"""
    module = load_publish_examples_module()
    console = Console(record=True, highlight=False)

    def raise_keyboard_interrupt(*, console: Console | None = None) -> int:
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "main", raise_keyboard_interrupt)

    assert module.run_entrypoint(console=console) == 130
    assert "已取消示例发布" in console.export_text()
