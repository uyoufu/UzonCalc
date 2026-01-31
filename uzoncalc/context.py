from typing import Any, Callable, Optional
import os
from .context_options import ContextOptions
from .cache.json_db import JsonDB
from .interaction import InteractionState, notify_observer


class CalcContext:
    def __init__(
        self,
        *,
        name: str | None = None,
        file_path: str | None = None,
        is_silent: bool = True,
    ):
        self.name = name or "calc_ctx" + hex(id(self))
        self.file_path = file_path

        # Notify observer if present
        notify_observer(self)

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
        self.vars = {"title": {}}

        # UI 交互相关状态
        self.interaction = InteractionState()

    @property
    def contents(self):
        return self.__contents

    # region content recording
    def append_content(self, content: str):
        if self.options.skip_content:
            return

        # 对 content 进行后处理
        for handler in self.options.post_handlers:
            content = handler.handle(content, ctx=self)

        # 若有 row_values，则添加到 row_values 中
        # 在其它地方将其转换成一行内容
        if self.__inline_values is not None:
            self.__inline_values.append(content)
            return

        self.__contents.append(content)

    def start_inline(self, separator: str = " "):
        self.__inline_separator = separator
        if self.__inline_values is not None:
            return

        self.__inline_values = []

    def end_inline(self):
        if self.__inline_values:
            combined = self.__inline_separator.join(self.__inline_values)
            # 将整行内容包装在 <p> 标签中
            self.__contents.append(f"<p>{combined}</p>")
            self.__inline_values = None

    @property
    def is_inline_mode(self) -> bool:
        """检查是否处于 inline 模式"""
        return self.__inline_values is not None

    # endregion

    # region result generation
    def html_content(self) -> str:
        return "\n".join(self.__contents)

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
