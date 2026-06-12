import importlib.util
from pathlib import Path

from uzoncalc import run_sync


def _load_help_module():
    """加载中文帮助文档示例模块。"""
    module_path = Path("examples/zh/help.zh.py")
    spec = importlib.util.spec_from_file_location("help_zh", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_help_zh_document_renders_core_sections():
    """中文帮助文档应渲染核心渐进章节和代表性组件。"""
    module = _load_help_module()

    ctx = run_sync(module.sheet)
    html = ctx.html_content()

    assert "UzonCalc 中文帮助文档" in html
    assert "最小计算书" in html
    assert "公式与单位" in html
    assert "表格与图表" in html
    assert "AI 编写计算书建议" in html
    assert "echart-container-" in html
    assert "<table" in html
    assert "data:image/png;base64" in html
    assert any(window.title == "结构参数输入" for window in ctx.ui_windows)
