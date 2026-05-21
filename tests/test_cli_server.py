import socket
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src/core"))

from uzoncalc import cli


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

    def fake_render_script_html(script_path_arg, output_path_arg):
        """模拟脚本重新渲染，验证监听器传递路径。"""
        assert script_path_arg == str(script_path)
        assert output_path_arg is None
        return next(rendered_html_values)

    monkeypatch.setattr(cli, "_render_script_html", fake_render_script_html)

    cli._watch_script_file_once(
        str(script_path),
        None,
        preview_state,
        last_mtime=script_path.stat().st_mtime - 1,
    )

    assert preview_state.get_html() == "<html>新内容</html>"
