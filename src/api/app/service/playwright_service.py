"""
Playwright 调用服务

缓存 Playwright 浏览器上下文，并为调用方提供自动释放页面的异步上下文。
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    async_playwright,
)

logger = logging.getLogger(__name__)

_STORAGE_STATE_PATH = Path("data/playwright/storage_state.json")

_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_context: Optional[BrowserContext] = None
_browser_lock = asyncio.Lock()
_storage_state_lock = asyncio.Lock()
_storage_state_tasks: set[asyncio.Task] = set()


@asynccontextmanager
async def allocate_page() -> AsyncIterator[Page]:
    """
    申请一个 Playwright 页面。

    调用方应使用 `async with allocate_page() as page:`，退出上下文时会自动关闭页面。
    """
    context = await _get_context()
    page = await context.new_page()
    try:
        yield page
    finally:
        await _close_page(page)
        _save_storage_state_in_background(context)


async def close_playwright_service():
    """
    关闭 Playwright 服务缓存的浏览器和运行时资源。
    """
    global _browser, _context, _playwright

    async with _browser_lock:
        context = _context
        browser = _browser
        playwright = _playwright
        _context = None
        _browser = None
        _playwright = None

    await _wait_storage_state_tasks()

    if context is not None:
        await _save_storage_state(context)
        await _close_context(context)

    if browser is not None:
        await _close_browser(browser)

    if playwright is not None:
        await playwright.stop()


async def _get_context() -> BrowserContext:
    """
    获取缓存的浏览器上下文；缓存不可用时重新创建。
    """
    global _browser, _context, _playwright

    async with _browser_lock:
        if _browser is not None and _browser.is_connected() and _context is not None:
            return _context

        if _browser is not None and not _browser.is_connected():
            _context = None
            _browser = None

        if _playwright is None:
            _playwright = await async_playwright().start()

        if _browser is None:
            _browser = await _playwright.chromium.launch(headless=True)

        _context = await _create_context(_browser)
        return _context


async def _create_context(browser: Browser) -> BrowserContext:
    """
    创建浏览器上下文，并在存在历史状态时加载 storage_state。
    """
    _STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _STORAGE_STATE_PATH.exists():
        return await browser.new_context(storage_state=str(_STORAGE_STATE_PATH))
    return await browser.new_context()


async def _close_page(page: Page):
    """
    关闭页面；已关闭页面不视为错误。
    """
    try:
        await page.close()
    except PlaywrightError as ex:
        if "has been closed" not in str(ex):
            raise


async def _close_context(context: BrowserContext):
    """
    关闭浏览器上下文；已关闭上下文不视为错误。
    """
    try:
        await context.close()
    except PlaywrightError as ex:
        if "has been closed" not in str(ex):
            raise


async def _close_browser(browser: Browser):
    """
    关闭浏览器；已关闭浏览器不视为错误。
    """
    try:
        await browser.close()
    except PlaywrightError as ex:
        if "has been closed" not in str(ex):
            raise


def _save_storage_state_in_background(context: BrowserContext):
    """
    投递后台 storage_state 保存任务，避免阻塞页面释放路径。
    """
    task = asyncio.create_task(_save_storage_state(context))
    _storage_state_tasks.add(task)
    task.add_done_callback(_finalize_storage_state_task)


def _finalize_storage_state_task(task: asyncio.Task):
    """
    清理后台保存任务，并记录保存失败信息。
    """
    _storage_state_tasks.discard(task)
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


async def _wait_storage_state_tasks():
    """
    等待已投递的后台 storage_state 保存任务收尾。
    """
    if not _storage_state_tasks:
        return

    await asyncio.gather(*list(_storage_state_tasks), return_exceptions=True)


async def _save_storage_state(context: BrowserContext):
    """
    将当前浏览器上下文状态保存到 storage_state 文件。
    """
    async with _storage_state_lock:
        _STORAGE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(_STORAGE_STATE_PATH))
