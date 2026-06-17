"""
Playwright 调用服务。

API 层只维护 core PlaywrightService 的单例包装，避免重复实现浏览器缓存逻辑。
"""

from pathlib import Path

from uzoncalc.service.playwright_service import PlaywrightService

_playwright_service = PlaywrightService(Path("data/playwright/storage_state.json"))


def allocate_page():
    """申请一个 Playwright 页面。"""
    return _playwright_service.allocate_page()


async def close_playwright_service():
    """关闭 Playwright 服务缓存的浏览器和运行时资源。"""
    await _playwright_service.close()
