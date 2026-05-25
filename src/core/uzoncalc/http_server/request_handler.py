"""HTML 预览请求处理器。"""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler


def create_html_request_handler(preview_state):
    """创建只返回当前 HTML 的 HTTP 处理器。"""

    class HtmlRequestHandler(BaseHTTPRequestHandler):
        """处理 HTML 预览请求。"""

        def do_GET(self):
            """返回 HTML 内容，未知路径返回 404。"""
            # 仅开放预览入口，避免误作为静态文件服务使用
            if self.path not in ("/", "/index.html"):
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            # 每次请求读取最新内容，支持静态预览和热更新预览
            html_bytes = preview_state.get_html().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def log_message(self, format, *args):
            """关闭 HTTP 请求日志，保持终端输出简洁。"""
            return

    return HtmlRequestHandler
