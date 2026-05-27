from app.controller.calc import calc_execution
from app.controller.calc.calc_dto import ExecutionResultResDTO
from app.sandbox.core.execution_result import ExecutionResult
from app.service.html_cache.html_cacher import HtmlContentPatchResult, HtmlUpdateType


class FakeHtmlCacher:
    """模拟 HTML 缓存器，避免控制器测试访问真实文件系统。"""

    def build_content_patch_from_paths(self, last_html_path: str | None, html_path: str):
        """返回固定补丁状态，验证控制器只负责响应字段整理。"""
        assert last_html_path == "public/calcs/1/old.html"
        assert html_path == "public/calcs/1/new.html"
        return HtmlContentPatchResult(
            updateType=HtmlUpdateType.Partial,
            contentHtml="<p>新结果</p>",
        )


def test_finalize_execution_result_builds_response_dto(monkeypatch):
    """控制器返回前转换响应 DTO，并清空原始 html 内容。"""
    monkeypatch.setattr(calc_execution, "html_cacher", FakeHtmlCacher())
    result = ExecutionResult(
        executionId="execution-id",
        html="<html>原始内容</html>",
        isCompleted=True,
        windows=[],
    )

    response_dto = calc_execution.finalize_execution_result_html(
        result,
        "public/calcs/1/old.html",
        "public/calcs/1/new.html",
    )

    assert isinstance(response_dto, ExecutionResultResDTO)
    assert response_dto.html == ""
    assert response_dto.htmlPath == "public/calcs/1/new.html"
    assert response_dto.updateType == HtmlUpdateType.Partial
    assert response_dto.htmlContentPatch == "<p>新结果</p>"
    assert not hasattr(result, "htmlPath")
