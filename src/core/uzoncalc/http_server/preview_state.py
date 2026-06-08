"""HTML 预览内容状态。"""

import threading


class HtmlPreviewState:
    """保存可更新 HTML，供监听线程和 HTTP 线程共享。"""

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


class StaticHtmlPreviewState:
    """保存静态 HTML，供 HTTP 处理器读取。"""

    def __init__(self, html_output: str):
        """初始化静态 HTML 内容。"""
        self._html_output = html_output

    def get_html(self) -> str:
        """读取静态 HTML 内容。"""
        return self._html_output
