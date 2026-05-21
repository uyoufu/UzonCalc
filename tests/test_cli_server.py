import socket
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))

from uzoncalc import cli, startup


def _read_preview_html(selected_port: int) -> str:
    """读取本地预览服务返回的 HTML 内容。"""
    response = urlopen(f"http://127.0.0.1:{selected_port}/", timeout=3)
    return response.read().decode("utf-8")


def test_create_html_server_uses_next_port_when_preferred_port_is_busy():
    """首选端口被占用时，应自动使用下一个可用端口。"""
    busy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    busy_socket.bind(("127.0.0.1", 0))
    busy_socket.listen(1)
    busy_port = busy_socket.getsockname()[1]

    try:
        server, selected_port = cli._create_html_server(
            cli.HtmlPreviewState("<html>ok</html>"), preferred_port=busy_port
        )
    finally:
        busy_socket.close()

    try:
        assert selected_port == busy_port + 1
    finally:
        server.server_close()


def test_html_server_returns_generated_html_at_root():
    """根路径应返回生成后的 HTML 文档。"""
    preview_state = cli.HtmlPreviewState("<html><body>计算结果</body></html>")
    server, selected_port = cli._create_html_server(preview_state, preferred_port=0)
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
    preview_state = cli.HtmlPreviewState("<html>旧内容</html>")
    server, selected_port = cli._create_html_server(preview_state, preferred_port=0)
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
    server, selected_port = cli._create_html_server(
        cli.HtmlPreviewState("<html>ok</html>"), preferred_port=0
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


def test_watch_script_file_updates_preview_state(tmp_path, monkeypatch):
    """脚本文件变动后，应重新渲染并更新预览状态。"""
    script_path = tmp_path / "calc_script.py"
    script_path.write_text("version = 1", encoding="utf-8")
    preview_state = cli.HtmlPreviewState("<html>旧内容</html>")
    rendered_html_values = iter(["<html>新内容</html>"])

    def fake_render_script_html(script_path_arg):
        """模拟脚本重新渲染，验证监听器传递路径。"""
        assert script_path_arg == str(script_path)
        return next(rendered_html_values)

    monkeypatch.setattr(cli, "_render_script_html", fake_render_script_html)

    cli._watch_script_file_once(
        str(script_path),
        preview_state,
        last_mtime=script_path.stat().st_mtime - 1,
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
