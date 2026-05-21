"""
UzonCalc CLI 入口

用法：
    uzoncalc path/to/script.py
    uzoncalc path/to/script.py --output path/to/output.html
"""

import argparse
import errno
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import inspect
import os
import sys
import threading
import time
import traceback

# 环境变量名：设置后 doc.save() 将变为空操作
_CLI_MODE_ENV = "UZONCALC_CLI_MODE"
_DEFAULT_SERVER_PORT = 32180
_SERVER_HOST = "127.0.0.1"
_WATCH_POLL_INTERVAL_SECONDS = 1.0


class HtmlPreviewState:
    """保存预览服务当前 HTML，供监听线程和 HTTP 线程共享。"""

    def __init__(self, html_output: str):
        """初始化当前 HTML 内容和线程锁。"""
        self._html_output = html_output
        self._lock = threading.Lock()

    def get_html(self) -> str:
        """读取当前 HTML 内容。"""
        with self._lock:
            return self._html_output

    def update_html(self, html_output: str):
        """更新当前 HTML 内容。"""
        with self._lock:
            self._html_output = html_output


def _load_module_from_path(script_path: str):
    """将脚本作为独立模块加载并返回，不执行顶层代码中的 if __name__=="__main__" 块"""
    spec = importlib.util.spec_from_file_location("_uzoncalc_script", script_path)

    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载脚本模块: {script_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _find_entry_functions(module) -> list:
    """查找模块中所有被 @uzon_calc 装饰过的入口函数"""
    entries = []
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if getattr(obj, "_uzon_calc_entry", False):
            entries.append(obj)
    return entries


def _render_ctx_html(ctx) -> str:
    """将 CalcContext 渲染为完整 HTML，逻辑与 doc.save() 一致"""
    from .template.utils import render_html_template

    # 统一 CLI 保存和预览服务使用的 HTML 渲染入口
    content = ctx.html_content()
    return render_html_template(content, ctx.options)


def _save_ctx(ctx, output_path: str | None, script_path: str) -> str:
    """将 CalcContext 渲染并保存为 HTML，逻辑与 doc.save() 一致"""
    # 确定文件名
    if output_path:
        filename = output_path
    else:
        # 默认：脚本所在目录 + 文档标题（或脚本名）
        title = (
            ctx.options.doc_title or os.path.splitext(os.path.basename(script_path))[0]
        )
        if not title.endswith(".html"):
            title += ".html"
        filename = os.path.join(os.path.dirname(script_path), title)

    if not filename.endswith(".html"):
        filename += ".html"

    filename = os.path.abspath(filename)

    # 渲染 HTML
    html_output = _render_ctx_html(ctx)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"Document saved to (open with browser): file:///{filename}")
    return html_output


def _render_script_html(script_path: str, output_path: str | None) -> str:
    """加载脚本、执行入口函数并返回保存后的 HTML。"""
    # 设置 CLI 模式环境变量，使脚本内 doc.save() 变为空操作
    os.environ[_CLI_MODE_ENV] = "1"
    try:
        module = _load_module_from_path(script_path)
    except Exception as e:
        print(f"Error: 脚本加载失败: {e}", file=sys.stderr)
        raise
    finally:
        os.environ.pop(_CLI_MODE_ENV, None)

    # 查找入口函数
    entries = _find_entry_functions(module)
    if not entries:
        raise RuntimeError("未找到 @uzon_calc 装饰的入口函数")

    # 执行所有入口函数并保存，多个入口时预览最后一个结果
    from .startup import run_sync

    html_output = ""
    for entry_fn in entries:
        try:
            ctx = run_sync(entry_fn)
        except Exception as e:
            print(
                f"Error: 入口函数 '{entry_fn.__name__}' 执行失败: {e}", file=sys.stderr
            )
            raise
        html_output = _save_ctx(ctx, output_path, script_path)
    return html_output


def _create_html_handler(preview_state: HtmlPreviewState):
    """创建只返回当前计算结果的 HTTP 处理器"""

    class CalcHtmlRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            # 仅开放预览入口，避免误作为静态文件服务使用
            if self.path not in ("/", "/index.html"):
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            # 每次请求读取最新内容，支持脚本变动后的热更新
            html_bytes = preview_state.get_html().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def log_message(self, format, *args):
            # 保持 CLI 输出简洁，只展示服务地址和错误信息
            return

    return CalcHtmlRequestHandler


def _create_html_server(
    preview_state: HtmlPreviewState, preferred_port: int = _DEFAULT_SERVER_PORT
) -> tuple[ThreadingHTTPServer, int]:
    """从首选端口开始创建本地 HTML 预览服务"""
    handler = _create_html_handler(preview_state)
    current_port = preferred_port

    while True:
        try:
            server = ThreadingHTTPServer((_SERVER_HOST, current_port), handler)
            selected_port = server.server_address[1]
            return server, selected_port
        except OSError as exc:
            if current_port == 0 or exc.errno != errno.EADDRINUSE:
                raise
            current_port += 1


def _watch_script_file_once(
    script_path: str,
    output_path: str | None,
    preview_state: HtmlPreviewState,
    last_mtime: float,
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
        html_output = _render_script_html(script_path, output_path)
    except Exception:
        # 渲染失败时保留上一版可用内容，便于用户修正脚本后继续预览
        traceback.print_exc()
        return current_mtime

    preview_state.update_html(html_output)
    print("Document reloaded.")
    return current_mtime


def _watch_script_file(
    script_path: str,
    output_path: str | None,
    preview_state: HtmlPreviewState,
    stop_event: threading.Event,
):
    """轮询脚本文件变动，直到服务停止。"""
    try:
        last_mtime = os.path.getmtime(script_path)
    except OSError:
        last_mtime = 0

    while not stop_event.wait(_WATCH_POLL_INTERVAL_SECONDS):
        last_mtime = _watch_script_file_once(
            script_path, output_path, preview_state, last_mtime
        )


def _serve_html(
    html_output: str,
    script_path: str,
    output_path: str | None,
    preferred_port: int = _DEFAULT_SERVER_PORT,
):
    """启动本地 HTTP 服务和文件监听，并阻塞直到用户中断"""
    preview_state = HtmlPreviewState(html_output)
    server, selected_port = _create_html_server(preview_state, preferred_port)
    stop_event = threading.Event()
    watch_thread = threading.Thread(
        target=_watch_script_file,
        args=(script_path, output_path, preview_state, stop_event),
        daemon=True,
    )
    watch_thread.start()
    print(f"Serving document at: http://{_SERVER_HOST}:{selected_port}/")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        stop_event.set()
        watch_thread.join(timeout=3)
        server.server_close()


def main():
    parser = argparse.ArgumentParser(
        prog="uzoncalc",
        description="运行 UzonCalc 计算脚本并导出 HTML 文档",
    )
    parser.add_argument(
        "script",
        help="要运行的 Python 脚本路径",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="输出 HTML 文件路径（省略时保存到脚本所在目录）",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help=f"启动本地 HTTP 预览服务（默认端口 {_DEFAULT_SERVER_PORT}，占用时自动递增）",
    )
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    if not os.path.isfile(script_path):
        print(f"Error: 脚本文件不存在: {script_path}", file=sys.stderr)
        sys.exit(1)

    output_path = os.path.abspath(args.output) if args.output else None

    # 将脚本所在目录加入 sys.path，支持同目录 import
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    try:
        html_output = _render_script_html(script_path, output_path)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise

    if args.server:
        _serve_html(html_output, script_path, output_path)


if __name__ == "__main__":
    main()
