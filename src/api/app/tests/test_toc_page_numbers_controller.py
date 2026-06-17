from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controller.calc import toc_page_numbers
from app.service.html_cache.html_cacher import HtmlCacher


def create_test_client() -> TestClient:
    """创建包含 ToC router 的测试应用。"""
    app = FastAPI()
    app.include_router(toc_page_numbers.router)
    return TestClient(app)


def test_api_toc_route_returns_api_compatible_response(monkeypatch, tmp_path: Path):
    """API 页码接口应与 CLI HTTP 使用相同路由尾部和返回结构。"""
    html_cacher = HtmlCacher()
    html_cacher.public_dir = tmp_path / "public"
    html_path = html_cacher.public_dir / "calcs" / "1" / "result.html"
    html_path.parent.mkdir(parents=True)
    html_path.write_text("<html>报告</html>", encoding="utf-8")

    calls = []

    async def fake_calculate(document_url: str):
        """模拟 core 页码计算。"""
        calls.append(document_url)
        return {"heading-0": 4}

    monkeypatch.setattr(toc_page_numbers, "html_cacher", html_cacher)
    monkeypatch.setattr(toc_page_numbers, "calculate_toc_page_numbers", fake_calculate)

    client = create_test_client()
    response = client.post(
        "/v1/calc/toc-page-numbers",
        json={"documentUrl": "http://localhost:3345/public/calcs/1/result.html"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "data": {"heading-0": 4},
        "message": "success",
        "code": 200,
    }
    assert calls == [html_path.resolve().as_uri()]


def test_api_toc_route_rejects_external_document_url():
    """API 页码接口不应允许任意外部 URL。"""
    client = create_test_client()

    response = client.post(
        "/v1/calc/toc-page-numbers",
        json={"documentUrl": "https://example.com/report.html"},
    )

    assert response.status_code == 400
