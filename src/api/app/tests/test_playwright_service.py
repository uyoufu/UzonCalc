import asyncio

from app.service import playwright_service


def test_api_playwright_service_delegates_to_core_singleton(monkeypatch):
    """API Playwright 服务应包装 core 单例，避免两套浏览器缓存实现。"""

    class FakeCoreService:
        def __init__(self):
            self.allocate_page_count = 0
            self.close_count = 0

        def allocate_page(self):
            """记录 API 是否委托页面申请。"""
            self.allocate_page_count += 1
            return "page-context"

        async def close(self):
            """记录 API 是否委托关闭。"""
            self.close_count += 1

    fake_service = FakeCoreService()
    monkeypatch.setattr(playwright_service, "_playwright_service", fake_service)

    assert playwright_service.allocate_page() == "page-context"
    asyncio.run(playwright_service.close_playwright_service())

    assert fake_service.allocate_page_count == 1
    assert fake_service.close_count == 1
