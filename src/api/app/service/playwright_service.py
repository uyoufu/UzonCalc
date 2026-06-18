"""
Playwright 调用服务。

API 层只维护 core PlaywrightService 的单例包装，避免重复实现浏览器缓存逻辑。
"""

from uzoncalc.service.playwright_service import (
    close_playwright_service as close_core_playwright_service,
    get_playwright_service,
)


def allocate_page():
    """申请一个 Playwright 页面。"""
    return get_playwright_service().allocate_page()


async def close_playwright_service():
    """关闭 Playwright 服务缓存的浏览器和运行时资源。"""
    await close_core_playwright_service()
