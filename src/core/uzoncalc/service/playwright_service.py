"""
Playwright 浏览器服务。

该服务缓存 Playwright 浏览器上下文，并允许调用方配置 storage_state 保存位置。
"""

from __future__ import annotations

import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    async_playwright,
)

logger = logging.getLogger(__name__)


class PlaywrightService:
    """缓存 Playwright 运行时、浏览器和上下文的服务。"""

    def __init__(self, storage_state_path: str | Path | None = None):
        """初始化服务，允许指定浏览器状态保存文件。"""
        self.storage_state_path = Path(
            storage_state_path or "data/playwright/storage_state.json"
        )
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._browser_lock = asyncio.Lock()
        self._storage_state_lock = asyncio.Lock()
        self._storage_state_tasks: set[asyncio.Task] = set()

    @asynccontextmanager
    async def allocate_page(self) -> AsyncIterator[Page]:
        """申请一个页面，并在退出上下文时自动关闭页面和保存状态。"""
        context = await self._get_context()
        page = await context.new_page()
        try:
            yield page
        finally:
            await self._close_page(page)
            self._save_storage_state_in_background(context)

    async def render_pdf_from_url(self, document_url: str) -> bytes:
        """打开文档 URL，并按打印样式渲染为 PDF 字节。"""
        async with self.allocate_page() as page:
            await page.goto(document_url, wait_until="networkidle")
            return await page.pdf(print_background=True, prefer_css_page_size=True)

    async def close(self):
        """关闭服务缓存的上下文、浏览器和 Playwright 运行时资源。"""
        async with self._browser_lock:
            context = self._context
            browser = self._browser
            playwright = self._playwright
            self._context = None
            self._browser = None
            self._playwright = None

        await self._wait_storage_state_tasks()

        if context is not None:
            await self._save_storage_state(context)
            await self._close_context(context)

        if browser is not None:
            await self._close_browser(browser)

        if playwright is not None:
            await playwright.stop()

    async def _get_context(self) -> BrowserContext:
        """获取缓存上下文，缓存不可用时重新创建。"""
        async with self._browser_lock:
            if (
                self._browser is not None
                and self._browser.is_connected()
                and self._context is not None
            ):
                return self._context

            if self._browser is not None and not self._browser.is_connected():
                self._context = None
                self._browser = None

            if self._playwright is None:
                self._playwright = await async_playwright().start()

            if self._browser is None:
                self._browser = await self._playwright.chromium.launch(headless=True)

            self._context = await self._create_context(self._browser)
            return self._context

    async def _create_context(self, browser: Browser) -> BrowserContext:
        """创建浏览器上下文，并在存在历史状态时加载 storage_state。"""
        self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
        if self.storage_state_path.exists():
            return await browser.new_context(storage_state=str(self.storage_state_path))
        return await browser.new_context()

    async def _close_page(self, page: Page):
        """关闭页面；已关闭页面不视为错误。"""
        try:
            await page.close()
        except PlaywrightError as ex:
            if "has been closed" not in str(ex):
                raise

    async def _close_context(self, context: BrowserContext):
        """关闭上下文；已关闭上下文不视为错误。"""
        try:
            await context.close()
        except PlaywrightError as ex:
            if "has been closed" not in str(ex):
                raise

    async def _close_browser(self, browser: Browser):
        """关闭浏览器；已关闭浏览器不视为错误。"""
        try:
            await browser.close()
        except PlaywrightError as ex:
            if "has been closed" not in str(ex):
                raise

    def _save_storage_state_in_background(self, context: BrowserContext):
        """投递后台 storage_state 保存任务，避免阻塞页面释放路径。"""
        task = asyncio.create_task(self._save_storage_state(context))
        self._storage_state_tasks.add(task)
        task.add_done_callback(self._finalize_storage_state_task)

    def _finalize_storage_state_task(self, task: asyncio.Task):
        """清理后台保存任务，并记录保存失败信息。"""
        self._storage_state_tasks.discard(task)
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except PlaywrightError:
            logger.exception("Save Playwright storage_state failed")
        except OSError:
            logger.exception("Write Playwright storage_state failed")
        except Exception:
            logger.exception("Unexpected Playwright storage_state save error")

    async def _wait_storage_state_tasks(self):
        """等待已投递的后台 storage_state 保存任务收尾。"""
        if not self._storage_state_tasks:
            return
        await asyncio.gather(*list(self._storage_state_tasks), return_exceptions=True)

    async def _save_storage_state(self, context: BrowserContext):
        """将当前浏览器上下文状态保存到 storage_state 文件。"""
        async with self._storage_state_lock:
            self.storage_state_path.parent.mkdir(parents=True, exist_ok=True)
            await context.storage_state(path=str(self.storage_state_path))


class ThreadedPlaywrightService:
    """在后台事件循环中复用 PlaywrightService，供同步调用方使用。"""

    def __init__(self, storage_state_path: str | Path | None = None):
        """初始化后台服务，延迟到首次调用时启动线程和事件循环。"""
        self.storage_state_path = storage_state_path
        self._thread_lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._service: PlaywrightService | None = None
        self._ready_event = threading.Event()
        self._startup_error: BaseException | None = None

    def render_pdf_from_url(self, document_url: str) -> bytes:
        """同步渲染 PDF，并保证底层异步服务运行在同一后台事件循环。"""
        service = self._get_service()
        loop = self._require_loop()
        future = asyncio.run_coroutine_threadsafe(
            service.render_pdf_from_url(document_url), loop
        )
        return future.result()

    def close(self):
        """关闭后台 Playwright 服务和事件循环。"""
        with self._thread_lock:
            loop = self._loop
            thread = self._thread
            service = self._service
            self._loop = None
            self._thread = None
            self._service = None
            self._ready_event.clear()

        if loop is None or thread is None:
            return

        if service is not None:
            future = asyncio.run_coroutine_threadsafe(service.close(), loop)
            future.result()

        loop.call_soon_threadsafe(loop.stop)
        thread.join()

    def _get_service(self) -> PlaywrightService:
        """获取后台事件循环中的 PlaywrightService 单例。"""
        self._ensure_started()
        if self._startup_error is not None:
            raise self._startup_error
        if self._service is None:
            raise RuntimeError("Playwright service did not start")
        return self._service

    def _require_loop(self) -> asyncio.AbstractEventLoop:
        """返回已启动的后台事件循环。"""
        if self._loop is None:
            raise RuntimeError("Playwright event loop did not start")
        return self._loop

    def _ensure_started(self):
        """按需启动后台线程，并等待事件循环和服务初始化完成。"""
        with self._thread_lock:
            if self._thread is not None:
                return

            self._ready_event.clear()
            self._startup_error = None
            self._thread = threading.Thread(
                target=self._run_loop,
                name="uzoncalc-playwright",
                daemon=True,
            )
            self._thread.start()

        self._ready_event.wait()

    def _run_loop(self):
        """后台线程入口：创建事件循环和异步 PlaywrightService。"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._loop = loop
            self._service = loop.run_until_complete(self._create_service())
        except BaseException as exc:
            self._startup_error = exc
            self._ready_event.set()
            loop.close()
            return

        self._ready_event.set()
        try:
            loop.run_forever()
        finally:
            loop.close()

    async def _create_service(self) -> PlaywrightService:
        """在后台事件循环中创建异步 Playwright 服务。"""
        return PlaywrightService(self.storage_state_path)
