"""脚本文件监听和热更新预览服务。"""

import os
import sys
import threading
import traceback
from typing import Callable

from .constants import DEFAULT_SERVER_PORT, SERVER_HOST, WATCH_POLL_INTERVAL_SECONDS
from .preview_state import HtmlPreviewState
from .server import create_html_server


def watch_script_file_once(
    script_path: str,
    preview_state: HtmlPreviewState,
    last_mtime: float,
    render_script_html: Callable[[str], str],
) -> float:
    """检查一次脚本文件变动，必要时重新渲染 HTML。"""
    try:
        current_mtime = os.path.getmtime(script_path)
    except OSError as e:
        print(f"Error: 监听脚本失败: {e}", file=sys.stderr)
        return last_mtime

    if current_mtime <= last_mtime:
        return last_mtime

    try:
        html_output = render_script_html(script_path)
    except Exception:
        # 渲染失败时保留上一版可用内容，便于用户修正脚本后继续预览
        traceback.print_exc()
        return current_mtime

    preview_state.update_html(html_output)
    print("Document reloaded.")
    return current_mtime


def watch_script_file(
    script_path: str,
    preview_state: HtmlPreviewState,
    stop_event: threading.Event,
    render_script_html: Callable[[str], str],
):
    """轮询脚本文件变动，直到服务停止。"""
    try:
        last_mtime = os.path.getmtime(script_path)
    except OSError:
        last_mtime = 0

    while not stop_event.wait(WATCH_POLL_INTERVAL_SECONDS):
        last_mtime = watch_script_file_once(
            script_path,
            preview_state,
            last_mtime,
            render_script_html,
        )


def serve_reloadable_html(
    html_output: str,
    script_path: str,
    render_script_html: Callable[[str], str],
    preferred_port: int = DEFAULT_SERVER_PORT,
):
    """启动本地 HTTP 服务和文件监听，并阻塞直到用户中断。"""
    preview_state = HtmlPreviewState(html_output)
    server, selected_port = create_html_server(preview_state, preferred_port)
    stop_event = threading.Event()
    watch_thread = threading.Thread(
        target=watch_script_file,
        args=(script_path, preview_state, stop_event, render_script_html),
        daemon=True,
    )
    watch_thread.start()
    print(f"Serving document at: http://{SERVER_HOST}:{selected_port}/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        stop_event.set()
        watch_thread.join(timeout=3)
        server.server_close()
