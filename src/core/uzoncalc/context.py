"""Calculation context state and user-facing document operations."""

from typing import Any, Callable, Optional
import os

from .template.utils import render_html_template
from .context_options import ContextOptions
from .cache.json_db import JsonDB
from .interaction import InteractionState
from .exporting import DocumentExporter, HtmlDocumentExporter
from .handcalc.post_handlers.dom_utils import (
    PostHandlerNode,
    parse_html_fragment,
    serialize_html_fragment,
)


class CalcContext:
    """Own calculation state, recorded content, options, and interactions."""

    def __init__(
        self,
        *,
        name: str | None = None,
        file_path: str | None = None,
        is_silent: bool = True,
        ctx_hook_created: Optional[Callable[["CalcContext"], Any]] = None,
        document_exporter: DocumentExporter | None = None,
    ) -> None:
        """Initialize an isolated calculation context.

        Args:
            name: Optional display name for the context.
            file_path: Source calculation file used for relative storage.
            is_silent: Whether UI calls should return defaults immediately.
            ctx_hook_created: Callback invoked after context initialization.
            document_exporter: Export strategy used by :meth:`save`.

        Returns:
            None.

        Raises:
            No exceptions are intentionally raised.
        """
        # 序列号，每次获取时增加 1
        self.serial_number = 0

        self.name = name or "calc_ctx" + hex(id(self))
        self.file_path = file_path

        # 静默执行
        self.is_silent = is_silent

        self.options = ContextOptions()

        # 记录结果
        self.__contents = []

        # 记录行内内容的临时存储
        self.__inline_values: list[str] | None = None
        self.__inline_separator: str = " "

        # ctx 使用的 json 缓存数据库
        self.json_db: None | JsonDB = None

        # 默认值存储
        # 每个 tile 中的上下文单独维护，以支持不同 tile 之间的默认值隔离
        self.vars: dict[str, dict[str, Any]] = {"title": {}}

        # UI 交互相关状态
        self.interaction = InteractionState()
        self._document_exporter = document_exporter or HtmlDocumentExporter()

        # 收集所有的 UI 定义（用于静默模式下返回所有 UI 定义）
        self.ui_windows: list[Any] = []

        # 创建时的回调
        if callable(ctx_hook_created):
            ctx_hook_created(self)

    @property
    def contents(self):
        return self.__contents

    # region content recording
    def append_content(self, content: str):
        if self.options.skip_content:
            return

        content = self._post_process_content(content)

        # 若有 row_values，则添加到 row_values 中
        # 在其它地方将其转换成一行内容
        if self.__inline_values is not None:
            self.__inline_values.append(content)
            return

        self.__contents.append(content)

    def _post_process_content(self, content: str) -> str:
        """Parse content once and let each post handler mutate DOM nodes."""
        if not self.options.post_handlers:
            return content

        root = parse_html_fragment(content)
        for node in list(root.iter()):
            post_node = PostHandlerNode(node)
            for handler in self.options.post_handlers:
                handler.handle(post_node, ctx=self)
        return serialize_html_fragment(root)

    def start_inline(self, separator: str = " "):
        """Start collecting subsequent content into one paragraph.

        Args:
            separator: Text inserted between collected fragments.

        Returns:
            None.

        Raises:
            No exceptions are intentionally raised.
        """
        if self.__inline_values is not None:
            return

        self.__inline_separator = separator
        self.__inline_values = []

    def end_inline(self):
        """Finish inline collection and restore normal content recording.

        Returns:
            None.

        Raises:
            No exceptions are intentionally raised.
        """
        if self.__inline_values is None:
            return

        inline_values = self.__inline_values
        self.__inline_values = None
        if inline_values:
            combined = self.__inline_separator.join(inline_values)
            # Inline fragments are already post-processed when appended.
            self.__contents.append(f"<p>{combined}</p>")

    @property
    def is_inline_mode(self) -> bool:
        """检查是否处于 inline 模式"""
        return self.__inline_values is not None

    # endregion

    # region result generation
    def html_content(self) -> str:
        html_content = "\n".join(self.__contents)
        for handler in self.options.context_result_handlers:
            html_content = handler.handle(html_content, ctx=self)
        return html_content

    def html(self) -> str:
        """
        获取完整 HTML 内容
        没有嵌入 css 样式
        css 样式通过模板引擎嵌入
        """
        return render_html_template(self.html_content(), self.options)

    def save(self, path: str) -> None:
        """Save the complete HTML document through the configured exporter.

        Args:
            path: Destination HTML path.

        Returns:
            None.

        Raises:
            OSError: If the destination cannot be written.
            ImportError: If ToC placeholders require unavailable dependencies.
        """
        self._document_exporter.export(self.html(), path)
        print(f"Document saved to (open with browser): file:///{path}")

    # endregion

    def get_location_dir(self) -> str:
        """
        获取当前上下文文件所在目录
        若 file_path 未设置，则返回当前工作目录
        """
        if self.file_path:
            return os.path.dirname(os.path.abspath(self.file_path))
        return os.getcwd()

    def get_json_db(self) -> JsonDB:
        """
        获取 SQLite 游标
        若尚未创建数据库连接，则创建一个内存数据库连接
        """
        if self.json_db is not None:
            return self.json_db

        dir = self.get_location_dir()

        # 开始连接
        self.json_db = JsonDB(os.path.join(dir, f"data/db.json"))
        return self.json_db

    def exit(self):
        """退出上下文，关闭数据库连接等"""
        if self.json_db is not None:
            self.json_db.save()

    def get_serial_number(self) -> int:
        """获取当前上下文的序列号"""
        self.serial_number += 1
        return self.serial_number
