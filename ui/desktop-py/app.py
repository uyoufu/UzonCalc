"""
UzonCalc Desktop Application

桌面应用主入口，负责启动 WebView 窗口和管理后台服务
"""

import html
import sys
from pathlib import Path

import webview

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import config
from js_api import JsApi
from service_manager import ServiceManager, get_service_manager
from logger import logger


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _load_template(template_name: str) -> str:
    """读取 HTML 模板文件"""
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    return template_path.read_text(encoding="utf-8")


def _build_welcome_html() -> str:
    """构建启动欢迎页"""
    app_name = html.escape(config.name)
    version = html.escape(config.version)
    template = _load_template("welcome.html")
    return template.replace("__APP_NAME__", app_name).replace(
        "__APP_VERSION__", version
    )


def _build_error_html(message: str) -> str:
    """构建启动失败页面"""
    safe_message = html.escape(message)
    app_name = html.escape(config.name)
    template = _load_template("error.html")
    return template.replace("__APP_NAME__", app_name).replace(
        "__ERROR_MESSAGE__", safe_message
    )


def _bootstrap_service(window, service_manager: ServiceManager):
    """在 WebView 启动后异步拉起后台服务"""
    try:
        logger.info("Starting API service in background...")
        if not service_manager.start():
            logger.error("Failed to start API service")
            window.load_html(_build_error_html("无法连接后台服务，请检查日志后重试。"))
            return

        logger.info("API service started, loading UI...")
        window.load_url(config.ui_url)
    except Exception as e:
        logger.error(f"An error occurred while starting service: {e}", exc_info=True)
        window.load_html(_build_error_html(str(e)))


def main():
    """主函数"""
    service_manager: ServiceManager | None = None

    try:
        # 获取服务管理器
        service_manager = get_service_manager()

        # 启动后台 API 服务
        logger.info("=" * 60)
        logger.info("UzonCalc Desktop Application Starting")
        logger.info("=" * 60)

        # 创建 JsApi 实例
        js_api = JsApi(service_manager)

        # 创建窗口（先展示欢迎页，后台启动服务后自动跳转）
        logger.info("Creating WebView window with welcome screen...")
        window = webview.create_window(
            config.name,
            html=_build_welcome_html(),
            js_api=js_api,
            width=config.width,
            height=config.height,
            resizable=True,
        )

        # 启动 WebView
        logger.info("Starting WebView...")
        webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
        webview.start(lambda: _bootstrap_service(window, service_manager), debug=True)

        logger.info("WebView closed by user")

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        # 清理资源，关闭后台服务
        logger.info("Cleaning up...")
        if service_manager:
            service_manager.cleanup()

        logger.info("=" * 60)
        logger.info("UzonCalc Desktop Application Stopped")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
