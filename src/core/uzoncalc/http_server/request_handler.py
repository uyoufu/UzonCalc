"""HTML 预览请求处理器。"""

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler

from ..service.toc_page_numbers import (
    TOC_PAGE_NUMBERS_ROUTE,
    calculate_toc_page_numbers_sync,
)


def _build_ok_response(data):
    """构造与 API ResponseResult 兼容的成功响应。"""
    return {"ok": True, "data": data, "message": "success", "code": 200}


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

        def do_POST(self):
            """处理本地预览服务的 JSON 请求。"""
            if self.path != TOC_PAGE_NUMBERS_ROUTE:
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                document_url = payload.get("documentUrl")
                if not isinstance(document_url, str) or not document_url:
                    self.send_error(HTTPStatus.BAD_REQUEST, "documentUrl is required")
                    return

                page_numbers = calculate_toc_page_numbers_sync(document_url)
                response_bytes = json.dumps(
                    _build_ok_response(page_numbers), ensure_ascii=False
                ).encode("utf-8")
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
                return

            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)

        def log_message(self, format, *args):
            """关闭 HTTP 请求日志，保持终端输出简洁。"""
            return

    return HtmlRequestHandler
