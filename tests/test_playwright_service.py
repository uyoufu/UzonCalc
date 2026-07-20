import asyncio
from pathlib import Path

from playwright.async_api import Error as PlaywrightError

from uzoncalc.service import playwright_service
from uzoncalc.service.playwright_service import (
    PlaywrightService,
    close_playwright_service,
    get_playwright_service,
)


class FakePage:
    """测试用页面对象，记录关闭状态。"""

    def __init__(self):
        self.close_count = 0

    async def close(self):
        """关闭测试页面。"""
        self.close_count += 1


class FakeBrowserContext:
    """测试用浏览器上下文，记录页面和 storage_state 状态。"""

    def __init__(self, new_context_kwargs: dict | None = None):
        self.new_context_kwargs = new_context_kwargs or {}
        self.new_page_count = 0
        self.close_count = 0
        self.storage_state_calls: list[dict] = []
        self.pages: list[FakePage] = []
        self.storage_state_started = asyncio.Event()
        self.storage_state_release = asyncio.Event()
        self.should_wait_storage_state = False

    async def new_page(self) -> FakePage:
        """创建一个新的测试页面。"""
        self.new_page_count += 1
        page = FakePage()
        self.pages.append(page)
        return page

    async def storage_state(self, **kwargs):
        """记录 storage_state 保存参数。"""
        self.storage_state_started.set()
        if self.should_wait_storage_state:
            await self.storage_state_release.wait()
        self.storage_state_calls.append(kwargs)

    async def close(self):
        """关闭测试上下文。"""
        self.close_count += 1


class FakeBrowser:
    """测试用浏览器对象，模拟 Playwright browser。"""

    def __init__(self, connected: bool = True):
        self.connected = connected
        self.new_context_count = 0
        self.close_count = 0
        self.contexts: list[FakeBrowserContext] = []

    def is_connected(self) -> bool:
        """返回浏览器是否仍可用。"""
        return self.connected

    async def new_context(self, **kwargs) -> FakeBrowserContext:
        """创建一个新的测试浏览器上下文。"""
        self.new_context_count += 1
        context = FakeBrowserContext(kwargs)
        self.contexts.append(context)
        return context

    async def close(self):
        """关闭测试浏览器。"""
        self.close_count += 1
        self.connected = False


class FakeChromium:
    """测试用 chromium 启动器。"""

    def __init__(self):
        self.launch_count = 0
        self.launch_kwargs_list: list[dict] = []
        self.launch_errors: list[PlaywrightError | None] = []
        self.browsers: list[FakeBrowser] = []

    async def launch(self, **kwargs) -> FakeBrowser:
        """创建测试浏览器并记录启动参数。"""
        self.launch_count += 1
        self.launch_kwargs_list.append(kwargs)
        if self.launch_errors:
            launch_error = self.launch_errors.pop(0)
            if launch_error is not None:
                raise launch_error
        browser = FakeBrowser()
        browser.launch_kwargs = kwargs
        self.browsers.append(browser)
        return browser


class FakePlaywright:
    """测试用 Playwright 根对象。"""

    def __init__(self):
        self.chromium = FakeChromium()
        self.stop_count = 0

    async def stop(self):
        """停止测试 Playwright。"""
        self.stop_count += 1


class FakePlaywrightFactory:
    """模拟 async_playwright() 返回的启动器。"""

    def __init__(self):
        self.start_count = 0
        self.playwright = FakePlaywright()

    async def start(self) -> FakePlaywright:
        """启动测试 Playwright。"""
        self.start_count += 1
        return self.playwright


def create_service(monkeypatch, storage_state_path: Path):
    """创建测试服务并注入 fake Playwright 工厂。"""
    factory = FakePlaywrightFactory()
    monkeypatch.setattr(playwright_service, "async_playwright", lambda: factory)
    return PlaywrightService(storage_state_path), factory


def test_allocate_page_returns_page_and_saves_state_in_background(monkeypatch, tmp_path):
    """申请页面应返回 Page，并在页面关闭后后台保存 storage_state。"""

    async def run_test():
        storage_state_path = tmp_path / "data" / "playwright" / "storage_state.json"
        service, factory = create_service(monkeypatch, storage_state_path)

        async with service.allocate_page() as first_page:
            assert isinstance(first_page, FakePage)
            assert first_page.close_count == 0

        browser = factory.playwright.chromium.browsers[0]
        context = browser.contexts[0]
        await context.storage_state_started.wait()

        async with service.allocate_page() as second_page:
            assert isinstance(second_page, FakePage)
            assert second_page is not first_page

        await service.close()

        assert first_page.close_count == 1
        assert second_page.close_count == 1
        assert factory.start_count == 1
        assert factory.playwright.chromium.launch_count == 1
        assert factory.playwright.chromium.launch_kwargs_list == [
            {"channel": "msedge", "headless": True}
        ]
        assert browser.new_context_count == 1
        assert context.new_page_count == 2
        assert context.storage_state_calls[0] == {"path": str(storage_state_path)}

    asyncio.run(run_test())


def test_allocate_page_fallbacks_to_playwright_chromium_when_edge_fails(
    monkeypatch,
    tmp_path,
):
    """系统 Edge 启动失败时，应回退到 Playwright Chromium。"""

    async def run_test():
        service, factory = create_service(monkeypatch, tmp_path / "storage.json")
        chromium = factory.playwright.chromium
        chromium.launch_errors.append(PlaywrightError("edge unavailable"))

        async with service.allocate_page():
            pass

        assert chromium.launch_kwargs_list == [
            {"channel": "msedge", "headless": True},
            {"headless": True},
        ]
        assert chromium.launch_count == 2

        await service.close()

    asyncio.run(run_test())


def test_allocate_page_reports_clear_error_when_edge_and_chromium_fail(
    monkeypatch,
    tmp_path,
):
    """系统 Edge 和 Playwright Chromium 都不可用时，应抛出清晰错误。"""

    async def run_test():
        service, factory = create_service(monkeypatch, tmp_path / "storage.json")
        chromium = factory.playwright.chromium
        chromium.launch_errors.extend(
            [
                PlaywrightError("edge unavailable"),
                PlaywrightError("chromium unavailable"),
            ]
        )

        try:
            async with service.allocate_page():
                pass
        except RuntimeError as ex:
            error_message = str(ex)
        else:
            raise AssertionError("Expected RuntimeError")

        assert "Microsoft Edge" in error_message
        assert "Playwright Chromium" in error_message
        assert "edge unavailable" in error_message
        assert "chromium unavailable" in error_message
        assert chromium.launch_kwargs_list == [
            {"channel": "msedge", "headless": True},
            {"headless": True},
        ]

    asyncio.run(run_test())


def test_allocate_page_does_not_wait_background_storage_save(monkeypatch, tmp_path):
    """页面关闭后的 storage_state 保存不应阻塞调用方继续执行。"""

    async def run_test():
        service, factory = create_service(monkeypatch, tmp_path / "storage.json")

        async with service.allocate_page():
            context = factory.playwright.chromium.browsers[0].contexts[0]
            context.should_wait_storage_state = True

        await asyncio.sleep(0)
        assert context.storage_state_started.is_set()
        assert context.storage_state_calls == []

        context.storage_state_release.set()
        await service.close()

    asyncio.run(run_test())


def test_allocate_page_loads_existing_storage_state(monkeypatch, tmp_path):
    """已有 storage_state 文件时，创建上下文应加载该文件。"""

    async def run_test():
        storage_state_path = tmp_path / "data" / "playwright" / "storage_state.json"
        storage_state_path.parent.mkdir(parents=True)
        storage_state_path.write_text('{"cookies": [], "origins": []}', encoding="utf-8")
        service, factory = create_service(monkeypatch, storage_state_path)

        async with service.allocate_page():
            pass

        browser = factory.playwright.chromium.browsers[0]
        await service.close()

        assert browser.contexts[0].new_context_kwargs == {
            "storage_state": str(storage_state_path)
        }

    asyncio.run(run_test())


def test_close_releases_context_browser_and_playwright(monkeypatch, tmp_path):
    """关闭服务应保存状态并释放上下文、浏览器和 Playwright。"""

    async def run_test():
        storage_state_path = tmp_path / "storage.json"
        service, factory = create_service(monkeypatch, storage_state_path)

        async with service.allocate_page():
            pass

        browser = factory.playwright.chromium.browsers[0]
        context = browser.contexts[0]
        await service.close()
        await service.close()

        assert context.storage_state_calls[-1] == {"path": str(storage_state_path)}
        assert context.close_count == 1
        assert browser.close_count == 1
        assert factory.playwright.stop_count == 1

    asyncio.run(run_test())


def test_close_waits_background_storage_save(monkeypatch, tmp_path):
    """关闭服务应等待页面关闭后投递的后台保存任务收尾。"""

    async def run_test():
        storage_state_path = tmp_path / "storage.json"
        service, factory = create_service(monkeypatch, storage_state_path)

        async with service.allocate_page():
            pass

        context = factory.playwright.chromium.browsers[0].contexts[0]
        context.should_wait_storage_state = True
        await context.storage_state_started.wait()

        close_task = asyncio.create_task(service.close())
        await asyncio.sleep(0)
        assert not close_task.done()

        context.storage_state_release.set()
        await close_task

        assert context.storage_state_calls[-1] == {"path": str(storage_state_path)}

    asyncio.run(run_test())


def test_allocate_page_recreates_disconnected_browser(monkeypatch, tmp_path):
    """浏览器断开连接后，再次申请页面应重新创建浏览器。"""

    async def run_test():
        service, factory = create_service(monkeypatch, tmp_path / "storage.json")

        async with service.allocate_page():
            pass

        first_browser = factory.playwright.chromium.browsers[0]
        first_browser.connected = False

        async with service.allocate_page():
            pass

        assert factory.start_count == 1
        assert factory.playwright.chromium.launch_count == 2
        assert factory.playwright.chromium.browsers[1] is not first_browser

        await service.close()

    asyncio.run(run_test())


def test_close_page_ignores_already_closed_page():
    """页面已关闭时，页面关闭操作不应抛出异常。"""

    class AlreadyClosedPage(FakePage):
        async def close(self):
            """模拟 Playwright 已关闭页面的错误。"""
            self.close_count += 1
            raise PlaywrightError("Target page, context or browser has been closed")

    async def run_test():
        service = PlaywrightService()
        page = AlreadyClosedPage()

        await service._close_page(page)

        assert page.close_count == 1

    asyncio.run(run_test())


def test_default_playwright_service_reuses_instance_in_running_loop(monkeypatch):
    """core 默认 Playwright 服务应在同一事件循环内复用实例。"""
    created_services = []

    class FakePlaywrightService:
        """记录默认服务的创建和关闭。"""

        def __init__(self, storage_state_path=None):
            self.storage_state_path = storage_state_path
            self.close_count = 0
            created_services.append(self)

        async def close(self):
            """记录默认服务关闭次数。"""
            self.close_count += 1

    async def run_test():
        first_service = get_playwright_service()
        second_service = get_playwright_service()

        assert first_service is second_service

        await close_playwright_service()
        third_service = get_playwright_service()

        assert third_service is not first_service
        await close_playwright_service()

    monkeypatch.setattr(playwright_service, "PlaywrightService", FakePlaywrightService)

    asyncio.run(run_test())

    assert len(created_services) == 2
    assert created_services[0].close_count == 1
    assert created_services[1].close_count == 1
