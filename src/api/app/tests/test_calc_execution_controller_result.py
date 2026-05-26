from app.controller.calc import calc_execution
from app.sandbox.core.execution_result import ExecutionResult


class FakeHtmlCacher:
    """模拟 HTML 缓存器，避免控制器测试访问真实文件系统。"""

    def build_content_patch_from_paths(self, last_html_path: str | None, html_path: str):
        """返回固定补丁，验证控制器只负责响应字段整理。"""
        assert last_html_path == "public/calcs/1/old.html"
        assert html_path == "public/calcs/1/new.html"
        return "<p>新结果</p>"


def test_finalize_execution_result_moves_cached_path_to_html_path(monkeypatch):
    """控制器返回前将缓存路径放入 htmlPath，并清空原始 html 内容。"""
    monkeypatch.setattr(calc_execution, "html_cacher", FakeHtmlCacher())
    result = ExecutionResult(
        executionId="execution-id",
        html="<html>原始内容</html>",
        isCompleted=True,
        windows=[],
    )

    calc_execution.finalize_execution_result_html(
        result,
        "public/calcs/1/old.html",
        "public/calcs/1/new.html",
    )

    assert result.html == ""
    assert result.htmlPath == "public/calcs/1/new.html"
    assert result.htmlContentPatch == "<p>新结果</p>"
