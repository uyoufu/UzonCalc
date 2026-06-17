import socket
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))

from uzoncalc import cli, startup
from uzoncalc.http_server import (
    HtmlPreviewState,
    create_html_server,
)
from uzoncalc.http_server.watcher import watch_script_file_once
from uzoncalc.service.toc_page_numbers import TOC_PAGE_NUMBERS_ROUTE


def _read_preview_html(selected_port: int) -> str:
    """读取本地预览服务返回的 HTML 内容。"""
    response = urlopen(f"http://127.0.0.1:{selected_port}/", timeout=3)
    return response.read().decode("utf-8")


def _post_json(selected_port: int, path: str, payload: str):
    """向本地预览服务提交 JSON 请求。"""
    request = Request(
        f"http://127.0.0.1:{selected_port}{path}",
        data=payload.encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return urlopen(request, timeout=3)


def test_create_html_server_uses_next_port_when_preferred_port_is_busy():
    """首选端口被占用时，应自动使用下一个可用端口。"""
    busy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    busy_socket.bind(("127.0.0.1", 0))
    busy_socket.listen(1)
    busy_port = busy_socket.getsockname()[1]

    try:
        server, selected_port = create_html_server(
            HtmlPreviewState("<html>ok</html>"), preferred_port=busy_port
        )
    finally:
        busy_socket.close()

    try:
        assert selected_port == busy_port + 1
    finally:
        server.server_close()


def test_html_server_returns_generated_html_at_root():
    """根路径应返回生成后的 HTML 文档。"""
    preview_state = HtmlPreviewState("<html><body>计算结果</body></html>")
    server, selected_port = create_html_server(preview_state, preferred_port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        response = urlopen(f"http://127.0.0.1:{selected_port}/", timeout=3)
        assert response.status == 200
        assert response.headers["Content-Type"] == "text/html; charset=utf-8"
        assert response.read().decode("utf-8") == "<html><body>计算结果</body></html>"
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_html_server_returns_latest_preview_state():
    """预览状态更新后，HTTP 服务应返回最新 HTML。"""
    preview_state = HtmlPreviewState("<html>旧内容</html>")
    server, selected_port = create_html_server(preview_state, preferred_port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        assert _read_preview_html(selected_port) == "<html>旧内容</html>"

        preview_state.update_html("<html>新内容</html>")

        assert _read_preview_html(selected_port) == "<html>新内容</html>"
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_html_server_returns_404_for_unknown_path():
    """未知路径应返回 404，避免误当作静态目录服务。"""
    server, selected_port = create_html_server(
        HtmlPreviewState("<html>ok</html>"), preferred_port=0
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        try:
            urlopen(f"http://127.0.0.1:{selected_port}/missing", timeout=3)
        except HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("unknown path should return 404")
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_html_server_toc_route_returns_api_compatible_response(monkeypatch):
    """CLI HTTP 页码接口应与 API 返回结构保持一致。"""
    preview_state = HtmlPreviewState("<html><body>计算结果</body></html>")
    calls = []

    async def fake_calculate(document_url: str):
        """模拟异步页码计算服务。"""
        calls.append(document_url)
        return {"heading-0": 3}

    monkeypatch.setattr(
        "uzoncalc.http_server.request_handler.calculate_toc_page_numbers",
        fake_calculate,
    )

    server, selected_port = create_html_server(preview_state, preferred_port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        response = _post_json(
            selected_port,
            TOC_PAGE_NUMBERS_ROUTE,
            '{"documentUrl":"http://127.0.0.1:%d/"}' % selected_port,
        )
        assert response.status == 200
        assert response.headers["Content-Type"] == "application/json; charset=utf-8"
        assert response.read().decode("utf-8") == (
            '{"ok": true, "data": {"heading-0": 3}, '
            '"message": "success", "code": 200}'
        )
        assert calls == [f"http://127.0.0.1:{selected_port}/"]
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_watch_script_file_updates_preview_state(tmp_path, monkeypatch):
    """脚本文件变动后，应重新渲染并更新预览状态。"""
    script_path = tmp_path / "calc_script.py"
    script_path.write_text("version = 1", encoding="utf-8")
    preview_state = HtmlPreviewState("<html>旧内容</html>")
    rendered_html_values = iter(["<html>新内容</html>"])

    def fake_render_script_html(script_path_arg):
        """模拟脚本重新渲染，验证监听器传递路径。"""
        assert script_path_arg == str(script_path)
        return next(rendered_html_values)

    watch_script_file_once(
        str(script_path),
        preview_state,
        last_mtime=script_path.stat().st_mtime - 1,
        render_script_html=fake_render_script_html,
    )

    assert preview_state.get_html() == "<html>新内容</html>"


def test_server_render_script_html_does_not_save_file(tmp_path, monkeypatch):
    """服务模式渲染应只返回内存 HTML，不写入输出文件。"""
    script_path = tmp_path / "calc_script.py"
    output_path = tmp_path / "result.html"
    script_path.write_text("version = 1", encoding="utf-8")

    class FakeOptions:
        """模拟 CalcContext 的 options。"""

    class FakeContext:
        """模拟 CalcContext 的 HTML 输出。"""

        options = FakeOptions()

        def html_content(self):
            """返回上下文正文 HTML。"""
            return "<body>计算结果</body>"

    def fake_load_module_from_path(script_path_arg):
        """模拟脚本模块加载。"""
        assert script_path_arg == str(script_path)
        return object()

    def fake_find_entry_functions(module):
        """模拟脚本中的计算入口函数。"""
        return [lambda: None]

    def fake_run_sync(entry_fn):
        """模拟入口函数执行结果。"""
        return FakeContext()

    def fake_render_ctx_html(ctx):
        """模拟上下文渲染结果。"""
        return f"<html>{ctx.html_content()}</html>"

    def fail_save_ctx(ctx, output_path_arg, script_path_arg):
        """服务模式不应调用保存函数。"""
        raise AssertionError("server render should not save html file")

    monkeypatch.setattr(cli, "_load_module_from_path", fake_load_module_from_path)
    monkeypatch.setattr(cli, "_find_entry_functions", fake_find_entry_functions)
    monkeypatch.setattr(cli, "_save_ctx", fail_save_ctx)
    monkeypatch.setattr(cli, "_render_ctx_html", fake_render_ctx_html)
    monkeypatch.setattr(startup, "run_sync", fake_run_sync)

    html_output = cli._render_script_html(str(script_path))

    assert html_output == "<html><body>计算结果</body></html>"
    assert not output_path.exists()


def test_static_html_server_does_not_start_file_watcher(monkeypatch):
    """静态预览服务应只启动 HTTP 服务，不创建文件监听线程。"""
    served_ports = []

    class FakeServer:
        """模拟阻塞式 HTTP 服务，避免测试长期占用线程。"""

        server_address = ("127.0.0.1", 34567)

        def serve_forever(self):
            """模拟用户中断服务。"""
            served_ports.append(self.server_address[1])
            raise KeyboardInterrupt

        def server_close(self):
            """记录服务已正常关闭。"""
            served_ports.append("closed")

    def fake_create_html_server(preview_state, preferred_port):
        """验证静态服务复用统一的 HTML 状态和端口探测入口。"""
        assert preview_state.get_html() == "<html>静态内容</html>"
        assert preferred_port == 0
        return FakeServer(), FakeServer.server_address[1]

    def fail_watch_script_file(*args, **kwargs):
        """静态服务不应启动文件监听。"""
        raise AssertionError("static server should not watch files")

    monkeypatch.setattr(
        "uzoncalc.http_server.server.create_html_server",
        fake_create_html_server,
    )
    monkeypatch.setattr(
        "uzoncalc.http_server.watcher.watch_script_file",
        fail_watch_script_file,
    )

    from uzoncalc.http_server.server import serve_static_html

    serve_static_html("<html>静态内容</html>", preferred_port=0)

    assert served_ports == [34567, "closed"]


def test_startup_view_runs_function_and_serves_rendered_html(monkeypatch):
    """view() 应执行计算函数、渲染 HTML，并启动无监听预览服务。"""
    calls = []

    class FakeContext:
        """模拟计算上下文。"""

        options = object()

        def html_content(self):
            """返回上下文正文 HTML。"""
            calls.append(("content",))
            return "<body>预览内容</body>"

    def fake_calc(arg_value, named_value=None):
        """模拟用户传入的计算入口。"""

    def fake_render_html_template(content, options):
        """验证 view() 使用模板渲染完整 HTML。"""
        assert content == "<body>预览内容</body>"
        assert options is fake_context.options
        calls.append(("render", content))
        return "<html>预览内容</html>"

    def fake_serve_static_html(html_output, preferred_port):
        """验证 view() 启动无监听服务。"""
        calls.append(("serve", html_output, preferred_port))

    fake_context = FakeContext()

    def fake_run_sync(func, *args, defaults=None, **kwargs):
        """验证 view() 透传计算函数参数。"""
        calls.append(("run", func, args, defaults, kwargs))
        return fake_context

    monkeypatch.setattr(startup, "run_sync", fake_run_sync)
    monkeypatch.setattr(
        "uzoncalc.template.utils.render_html_template", fake_render_html_template
    )
    monkeypatch.setattr(
        "uzoncalc.http_server.server.serve_static_html", fake_serve_static_html
    )

    startup.view(
        fake_calc,
        "参数",
        defaults={"默认": {"值": 1}},
        preferred_port=0,
        named_value="命名参数",
    )

    assert calls == [
        (
            "run",
            fake_calc,
            ("参数",),
            {"默认": {"值": 1}},
            {"named_value": "命名参数"},
        ),
        ("content",),
        ("render", "<body>预览内容</body>"),
        ("serve", "<html>预览内容</html>", 0),
    ]


def test_package_exports_view():
    """包顶层应导出 view()，便于用户脚本直接导入。"""
    import uzoncalc

    assert uzoncalc.view is startup.view


def test_startup_does_not_import_cli_module():
    """startup.py 不应依赖 cli.py，避免核心入口反向加载 CLI。"""
    startup_source = Path(startup.__file__).read_text("utf-8")

    assert "from .cli import" not in startup_source
