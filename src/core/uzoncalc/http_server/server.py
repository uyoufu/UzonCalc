"""HTML 预览服务创建和生命周期。"""

import errno
from http.server import ThreadingHTTPServer

from .constants import DEFAULT_SERVER_PORT, SERVER_HOST
from .preview_state import StaticHtmlPreviewState
from .request_handler import create_html_request_handler


def create_html_server(
    preview_state,
    preferred_port: int = DEFAULT_SERVER_PORT,
) -> tuple[ThreadingHTTPServer, int]:
    """从首选端口开始创建本地 HTML 预览服务。"""
    handler = create_html_request_handler(preview_state)
    current_port = preferred_port

    # 首选端口被占用时顺延查找，preferred_port=0 时交给系统分配
    while True:
        try:
            server = ThreadingHTTPServer((SERVER_HOST, current_port), handler)
            selected_port = server.server_address[1]
            return server, selected_port
        except OSError as exc:
            if current_port == 0 or exc.errno != errno.EADDRINUSE:
                raise
            current_port += 1


def serve_static_html(
    html_output: str,
    preferred_port: int = DEFAULT_SERVER_PORT,
):
    """启动无文件监听的本地 HTTP 预览服务，并阻塞直到用户中断。"""
    # 静态预览只服务当前这次计算得到的 HTML
    preview_state = StaticHtmlPreviewState(html_output)
    server, selected_port = create_html_server(preview_state, preferred_port)
    print(f"Serving document at: http://{SERVER_HOST}:{selected_port}/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
